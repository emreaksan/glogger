## The poor man's book keeper
A lightweight logging utility for dumping structured data into Google Sheet.


### Installation
Run `python setup.py install`

### Setup
Set `GDRIVE_API_KEY` environment variable to your private credential file. How you create it is explained below. 
Do not share this file or make it publicly available as it is supposed to be a private key file.

You also need to know about `workbook id` and `sheet name` which are explained below. 
Please have a look at the provided example `tests/example_run.py` to see how you can 
use this package.

For every entry (i.e., row), it expects a unique identifier which is later used to find the same row and update entries.
The entries should be given in a dictionary format where the keys correspond to the column headers. If a particular
header does not exist, it is created automatically.  
 

####Credential file
If you don't have a Google Sheet Credential JSON:
1. Go to https://console.developers.google.com
2. Create a project if you don't have any. 
   1. Click on `Select a project` on top-left and then click `NEW PROJECT` on the pop-up window.
   2. Enter a project name and continue. Location section is irrelevant.  
   3. The project you just created should be selected automatically. If not, select it and continue with the next step.
3. Click on `ENABLE APIS AND SERVICES`
4. Search for Google Sheets API and navigate.
5. Enable it.
6. On the next window, click on `Create Credentials` button.
   1. Answers to the questions on this page: Google Sheets API, Web server, Application data and No. Click on `What credentials do I need?` button
   2. Enter a name for the service account and assign Project > Editor role. Select `JSON` as the key type and continue.
   3. Your JSON key file is downloaded automatically. Keep it wisely.


If you have a Google Sheet Credential JSON:
1. In the JSON key file, you will see `client_email` entry. Google Sheet files must be shared with this account in order to get access. Similarly, you can simply add accounts of the other contributors.
   1. Click on `Share` on top-right.
   2. Enter `client_email` and share with `Editor` permission.
2. Or, you can make your Google Sheet publicly available. Everyone with your file's **workbook** id can access.
   1. Click on `Share` on top-right.
   2. Under the `Get link` section, click on `Change` and select `Anyone with the link` option with `Editor` role.

####Workbook 
You can create a Google Sheet file in your Google Drive. The workbook address can be found in the URL as follows: 
docs.google.com/spreadsheets/d/`1Ppq9okztrceM2Ym2UAz_GQfRKKmJUx3O4R9IFKGUvXw`/edit#gid=0 

####Sheet 
The sheet name is by default `Sheet1` for a new file where you can give any names. 