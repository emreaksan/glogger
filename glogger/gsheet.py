"""Dumps entries into Google Sheet."""

import copy
import json
import socket
import time
import traceback

import gspread
import numpy as np
from google.auth.transport.requests import AuthorizedSession
from google.oauth2 import service_account


class GoogleSheetLogger(object):
    """Log selected outputs to a predefined Google Sheet.
  
    2019 - Modified by Emre.
    2019 - Updated by Wookie.
    2018 - Initialized by Emre.
    """

    def __init__(self,
                 credential_file,
                 workbook_key,
                 sheet_name,
                 identifier_key,
                 identifier=None,
                 static_values=None,
                 config_sheet_name=None):
        """Creates an initial entry.
    
        Args:
          credential_file: path to json API key.
          workbook_key: google sheet key (in URL).
          sheet_name: name of sheet to be edited.
          identifier_key: Column name to store unique entry identifier.
          identifier: unique entry id. if provided, an entry is created immediately.
          static_values (dict): columns and values that don't change. These values will be written every time
            a new row is appended, no matter in which sheet we are logging.
          config_sheet_name: If provided, config parameters will be stored in this worksheet, otherwise they
            go into the default worksheet `sheet_name`.
        """
        self.credential_file = credential_file
        self.workbook_key = workbook_key
        self.sheet_name = sheet_name
        self.identifier_key = identifier_key
        self.identifier = identifier
        self.config_sheet_name = config_sheet_name

        self.start_time = time.strftime('%Y/%m/%d %H:%M:%S')
        self.hostname = socket.getfqdn()
        self.static_values = static_values if static_values is not None else dict()
        self.credential_key = json.load(self.credential_file)

        try:
            credentials = service_account.Credentials.from_service_account_info(
                self.credential_key,
                scopes=['https://www.googleapis.com/auth/spreadsheets'])

            self.client = gspread.Client(auth=credentials)
            self.client.session = AuthorizedSession(credentials)
        except:  # pylint: disable=bare-except
            print('Could not authenticate with Drive API.')
            traceback.print_exc()

        self.static_values['Hostname'] = self.hostname
        self.static_values['Start Time'] = self.start_time
        if self.identifier is not None:
            self.static_values[self.identifier_key] = self.identifier

        # If the entry identifier is already provided, create an entry.
        self.ready = True
        if self.identifier is not None:
            try:
                self.update(self.static_values, self.sheet_name)
            except:  # pylint: disable=bare-except
                self.ready = False
                traceback.print_exc()
                return

    def update_config_vals(self, config_values):
        """Update the hyperparameters."""
        sheet_name = self.sheet_name if self.config_sheet_name is None else self.config_sheet_name
        self._write(config_values, sheet_name)

    def update(self, values, sheet_name=None, config_values=None):
        """
        Updates an existing row or creates a new one. If `self.identifier` is found in the column named
          `self.identifier_key` that row is updated, otherwise a new one is appended.

        Args:
            values (dict): The values to write into `sheet_name`.
            sheet_name: Name of the worksheet to write into, defaults to `self.sheet_name`.
            config_values: If provided, the hyperparameters in `self.config_sheet_name` are upated.
        """
        assert isinstance(values, dict)

        if not self.ready:  # Silently skip if init failed
            return

        sheet_name = sheet_name if sheet_name is not None else self.sheet_name
        self._write(values, sheet_name)

        if config_values is not None:
            config_sheet_name = self.config_sheet_name if self.config_sheet_name is not None else sheet_name
            self._write(config_values, config_sheet_name)

    def _write(self, values, sheet_name):
        """Write a dictionary into the given worksheet."""
        vals = copy.deepcopy(values)
        vals.update(self.static_values)
        
        # Timestamp.
        vals['Last Updated'] = time.strftime('%Y/%m/%d %H:%M:%S')

        # Authenticate
        try:
            credentials = service_account.Credentials.from_service_account_info(
                self.credential_key,
                scopes=['https://www.googleapis.com/auth/spreadsheets'])

            self.client = gspread.Client(auth=credentials)
            self.client.session = AuthorizedSession(credentials)
        except:  # pylint: disable=bare-except
            print('Could not authenticate with Drive API.')
            traceback.print_exc()

        try:
            # Find a workbook by name.
            workbook = self.client.open_by_key(self.workbook_key)
            sheet = workbook.worksheet(sheet_name)
        except:  # pylint: disable=bare-except
            print('Could not open sheet ' + sheet_name)
            traceback.print_exc()
            self.ready = False
            return

        identifier = self.static_values[self.identifier_key]

        try:
            header = sheet.row_values(1)
            identifier_idx = header.index(self.identifier_key) + 1
            row_index = sheet.col_values(identifier_idx).index(str(identifier))
        except:  # pylint: disable=bare-except
            try:
                header = sheet.row_values(1)
                row_index = len(sheet.col_values(1))
            except gspread.exceptions.APIError:
                # Probably quota exceeded.
                return

        # The header is always on the first row. So if the sheet is empty, we must make sure actual data only starts
        # from the 2nd line on.
        row_index = max(row_index, 1)

        # If the cells are not in order with respect to their column IDs, the API
        # yields unexpected results, i.e., deleting/overwriting other rows, etc.
        # It is best to make separate requests for the cells from different rows.
        headers_to_create = list()
        cells_to_update = [None] * len(header)
        # Construct new row
        for key in sorted(vals.keys()):
            value = vals[key]
            if key not in header:
                header.append(key)
                cells_to_update.append(None)
                headers_to_create.append(gspread.models.Cell(1, len(header), key))

            col_index = header.index(key)
            if isinstance(value, np.generic):
                if np.isnan(value):
                    col_value = 'NaN'
                elif np.isinf(value):
                    col_value = 'Inf'
                else:
                    col_value = np.asscalar(value)

            elif isinstance(value, np.ndarray) and value.ndim == 0:
                col_value = value.item()
            elif isinstance(value, str):
                col_value = value
            elif hasattr(value, '__len__') and value:
                col_value = str(value)
            else:
                col_value = value

            cells_to_update[col_index] = gspread.models.Cell(
                row_index + 1, col_index + 1, value=col_value)

        try:
            if cells_to_update:
                sheet.update_cells(list(filter(None, cells_to_update)))
            if headers_to_create:
                sheet.update_cells(headers_to_create)
        except gspread.exceptions.APIError:
            # Probably quota exceeded.
            pass
