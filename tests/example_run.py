import os
import time
from glogger.gsheet import GoogleSheetLogger


key_file = os.environ.get("GDRIVE_API_KEY", None)
assert key_file is not None, "GDRIVE_API_KEY environment variable is not set."

# I leave this file publicly available. You can run the test either with your
# own file or on this one. It can be visited at
# https://docs.google.com/spreadsheets/d/1Ppq9okztrceM2Ym2UAz_GQfRKKmJUx3O4R9IFKGUvXw/edit?usp=sharing

# If you will use this file and don't change experiment_id below,
# it will be overwritten.

workbook = "1Ppq9okztrceM2Ym2UAz_GQfRKKmJUx3O4R9IFKGUvXw"
sheet = "sheet_with_a_custom_name"
# Column to enter the unique identifier. For every new request, it will first
# check this column whether there is already an entry or not.
identifier_key = "Experiment ID"
experiment_id = "1234567891"  # a unique experiment identifier

glogger = GoogleSheetLogger(
          credential_file=open(key_file, "r"),
          workbook_key=workbook,
          sheet_name=sheet,
          identifier_key=identifier_key,
          identifier=experiment_id)

# Dump if there are some static entries. Note that static entries can also be
# part of the dynamic entries.
static_entries = dict(comment="glogger_test_run")
glogger.set_static_cells(static_entries)

# Entries changing over time such as loss values. It expects dictionaries where
# the keys correspond to the column headers.
for i in range(5):
  losses = dict(a_loss=i, b_loss=2.2*i)
  glogger.update_or_append_row(losses)
  
  # Wait for 2 seconds.
  # Check your Google Sheet in the meantime to observe the updates.
  time.sleep(2)
