"""Dumps entries into Google Sheet."""

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
               static_values=None):
    """Creates an initial entry.

    Args:
      credential_file: path to json API key.
      workbook_key: google sheet key (in URL).
      sheet_name: name of sheet to be edited.
      identifier_key: Column name to store unique entry identifier.
      identifier: unique entry id. if provided, an entry is created immediately.
      static_values (dict): columns and values that don't change.
    """
    self.credential_file = credential_file
    self.workbook_key = workbook_key
    self.sheet_name = sheet_name
    self.identifier_key = identifier_key
    self.identifier = identifier
    
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
    
    # Create the first entry.
    if static_values:
      for key, val in static_values.items():
        self.static_values[key] = val
    
    self.static_values['Hostname'] = self.hostname
    self.static_values['Start Time'] = self.start_time
    if self.identifier is not None:
      self.static_values[self.identifier_key] = self.identifier
      
    # If the entry identifier is already provided, create an entry.
    self.ready = True
    if self.identifier is not None:
      try:
        self.update_or_append_row(self.static_values, self.sheet_name)
      except:  # pylint: disable=bare-except
        self.ready = False
        traceback.print_exc()
        return
  
  def set_static_cells(self, static_dict):
    for key, val in static_dict.items():
      self.static_values[key] = val
    self.update_or_append_row(self.static_values, self.sheet_name)
  
  def update_or_append_row(self, values, sheet_name=None):
    """Updates an existing entry or creates one (defined by the identifier)."""
    assert isinstance(values, dict)
    
    if not self.ready:  # Silently skip if init failed
      return
    
    if not sheet_name:
      sheet_name = self.sheet_name
    
    values.update(self.static_values)
    values['Last Updated'] = time.strftime('%Y/%m/%d %H:%M:%S')
    
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
    
    identifier = values[self.identifier_key]
    
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
    
    # If the cells are not in order with respect to their column IDs, the API
    # yields unexpected results, i.e., deleting/overwriting other rows, etc.
    # It is best to make separate requests for the cells from different rows.
    headers_to_create = list()
    cells_to_update = [None]*len(header)
    # Construct new row
    for key in sorted(values.keys()):
      value = values[key]
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