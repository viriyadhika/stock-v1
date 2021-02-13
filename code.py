import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import datetime
import time
import os
import shutil

#These are the headers for all computer generated files
STANDARD_TICKER = 'Ticker'
STANDARD_DATE = 'Date'
STANDARD_CLOSE = 'Close'
STANDARD_BVS = 'BVS'

#below is directory for BVS latest update file
BVS_DIR = 'bvs'
BVS_FILE_NAME = 'bvs'
BVS_FILE_FORMAT = '.csv'

#back up directory before any data was processed
BACKUP_DIR = 'backup'

#below is the sheet which the graph will pull data from
FINAL_FILE_DIR = 'csv'
FINAL_FILE_EXT = '.csv'

#constants related to image processing (graph generation)
IMAGE_DIR = 'images'
IMAGE_EXT = '.png'

def update_daily_price():
  TICKER = '<ticker>'
  DATE = '<date>'
  CLOSE = '<close>'

  data = pd.read_csv('MS210111.txt')
  data = data[[TICKER, DATE, CLOSE]]
  data[DATE] = pd.to_datetime(data[DATE], format='%m/%d/%Y')
  data.rename(columns = {DATE: STANDARD_DATE, CLOSE: STANDARD_CLOSE}, inplace=True)

  for i in data.index:
    this_row = data.iloc[i]
    ticker_name = this_row[TICKER].lower()
    new_data = update_or_create_company_price(
      ticker_name
      )
    new_data = new_data.reset_index()
    
    new_entry = this_row[[STANDARD_DATE, STANDARD_CLOSE]]
    new_entry[STANDARD_BVS] = get_bvs(ticker_name)
    new_data = new_data.append(new_entry, ignore_index=True)

    new_data.set_index(STANDARD_DATE, inplace=True)
    new_data = new_data[~new_data.index.duplicated(keep='last')]
    new_data.sort_index(inplace=True)

    new_data.to_csv(FINAL_FILE_DIR + '/' + ticker_name + FINAL_FILE_EXT)
    print('CSV file updated for: ' + ticker_name + '!')

def get_bvs(ticker):
  try:
    data = pd.read_csv(BVS_DIR + '/' + BVS_FILE_NAME + BVS_FILE_FORMAT)
    data.set_index(STANDARD_TICKER, inplace=True)
    try:
      return data.loc[ticker][STANDARD_BVS]
    except KeyError:
      return np.nan
  except FileNotFoundError:
    print(BVS_DIR + '/' + BVS_FILE_NAME + BVS_FILE_FORMAT + ' not found! Please create it!')

def update_or_create_company_price(ticker):
  try:
    #Check if final file is there
    data = pd.read_csv((FINAL_FILE_DIR + '/' + ticker + FINAL_FILE_EXT))
    data[STANDARD_DATE] = pd.to_datetime(data[STANDARD_DATE])
    return update_company_price(data, ticker)
  except FileNotFoundError:
    #final file not there
    return create_company_price(ticker)

def update_company_price(final_data, ticker):
  try:
    #check if 999 file is there
    data = pd.read_csv((ticker + FINAL_FILE_EXT))
    final_data = combine_final_with_raw(final_data, data, ticker)
    return final_data
  except FileNotFoundError:
    # there's no 999 file, do nothing
    final_data.set_index(STANDARD_DATE, inplace=True)
    return final_data

def combine_final_with_raw(final_data, data, ticker):
  RAW_DATA_DATE = 'Date'
  RAW_DATA_CLOSE = 'Close'

  final_data = final_data[[STANDARD_DATE, STANDARD_CLOSE, STANDARD_BVS]]
  data = data.loc[:,[RAW_DATA_DATE, RAW_DATA_CLOSE]]
  data.rename(columns = {RAW_DATA_DATE: STANDARD_DATE, RAW_DATA_CLOSE: STANDARD_CLOSE}, inplace=True)
  data.loc[data[STANDARD_CLOSE] < 50, [STANDARD_CLOSE]] = data.loc[data[STANDARD_CLOSE] < 50, [STANDARD_CLOSE]] * 1000
  data[STANDARD_DATE] = pd.to_datetime(data[STANDARD_DATE], format='%m/%d/%Y')
  data[STANDARD_BVS] = np.nan

  data.set_index(STANDARD_DATE, inplace=True)
  final_data.set_index(STANDARD_DATE, inplace=True)

  data.update(final_data)

  final_data = pd.concat([data, final_data])
  final_data = final_data[~final_data.index.duplicated(keep='first')]
  final_data.sort_index(inplace=True)

  return final_data

def create_company_price(ticker):
  RAW_DATA_DATE = 'Date'
  RAW_DATA_CLOSE = 'Close'

  try:
    #check if 999 file is there
    data = pd.read_csv(ticker + FINAL_FILE_EXT)
    data.rename(columns = {RAW_DATA_DATE: STANDARD_DATE, RAW_DATA_CLOSE: STANDARD_CLOSE}, inplace=True)
    data = data[[STANDARD_DATE, STANDARD_CLOSE]]
    data[STANDARD_BVS] = np.nan
    data.loc[data[STANDARD_CLOSE] < 50, [STANDARD_CLOSE]] = data.loc[data[STANDARD_CLOSE] < 50, [STANDARD_CLOSE]] * 1000
    data[STANDARD_DATE] = pd.to_datetime(data[STANDARD_DATE], format='%m/%d/%Y')
    data.set_index(STANDARD_DATE, inplace=True)

    return data

  except FileNotFoundError:
    data = pd.DataFrame(columns=[STANDARD_DATE, STANDARD_CLOSE, STANDARD_BVS])
    data.set_index(STANDARD_DATE, inplace=True)
    return data

def update_bvs():
  TICKER = '<ticker>'
  DATE_FROM = '<from>'
  DATE_TO = '<to>'
  BVS = '<bvs>'
  BVS_UPDATE_FILE = 'bvs.csv'
  
  data = pd.read_csv(BVS_UPDATE_FILE)
  data[DATE_FROM] = pd.to_datetime(data[DATE_FROM], format='%m/%d/%Y')
  data[DATE_TO] = pd.to_datetime(data[DATE_TO], format='%m/%d/%Y')
  data.rename(columns = {BVS: STANDARD_BVS}, inplace=True)

  for i in data.index:
    this_row = data.iloc[i]
    update_company_bvs(
      this_row[TICKER].lower(),
      this_row[[DATE_FROM, DATE_TO, STANDARD_BVS]],
      DATE_TO,
      DATE_FROM
    )

def update_company_bvs(ticker, new_entry, DATE_TO, DATE_FROM):
  try:
    data = pd.read_csv(FINAL_FILE_DIR + '/' + ticker + FINAL_FILE_EXT)
    data[STANDARD_DATE] = pd.to_datetime(data[STANDARD_DATE])

    if (STANDARD_BVS not in data.columns.tolist()):
      data[STANDARD_BVS] = None

    filtered_data = data.loc[(
      data[STANDARD_DATE] <= new_entry[DATE_TO]
      ) & (
        data[STANDARD_DATE] >= new_entry[DATE_FROM]
        ), (STANDARD_BVS)]

    filtered_data = filtered_data.apply(lambda x: new_entry[STANDARD_BVS])
    data.update(filtered_data)
    data.set_index(STANDARD_DATE, inplace=True)
    data.to_csv(FINAL_FILE_DIR + '/' + ticker + FINAL_FILE_EXT)

  except FileNotFoundError:
    print('The file ' + FINAL_FILE_DIR + '/' + ticker + FINAL_FILE_EXT + " is not found. BVS can't be updated for this ticker!" + '\n\
      Please create this record first before re-running this command' \
    )

  try:
    data = pd.read_csv(BVS_DIR + '/' + BVS_FILE_NAME + BVS_FILE_FORMAT)
    data[STANDARD_DATE] = pd.to_datetime(data[STANDARD_DATE])

    if ticker in data[STANDARD_TICKER].values:
      data.set_index(STANDARD_TICKER, inplace=True)
      if data.loc[ticker][STANDARD_DATE] <= new_entry[DATE_TO]:
        new_entry_df = pd.DataFrame(
          {
            STANDARD_DATE: [new_entry[DATE_TO].strftime('%Y-%m-%d')],
            STANDARD_TICKER: [ticker],
            STANDARD_BVS: [new_entry[STANDARD_BVS]]
          }
        )
        new_entry_df.set_index(STANDARD_TICKER,inplace=True)
        data.update(new_entry_df)
    else:
      new_data = pd.DataFrame({
        STANDARD_DATE: [new_entry[DATE_TO]], 
        STANDARD_BVS: [new_entry[STANDARD_BVS]],
        STANDARD_TICKER: [ticker]
        })
      data = data.append(new_data, ignore_index=True)
      data.set_index(STANDARD_TICKER, inplace=True)
    
    data.to_csv(BVS_DIR + '/' + BVS_FILE_NAME + BVS_FILE_FORMAT)
    print('BVS updated for ' + ticker)

  except FileNotFoundError:
    print('BVS database is not found, please:\n\
      1. Create a folder with the name ' + BVS_DIR + '\n\
      2. In the folder, create a file with the name ' + BVS_FILE_NAME + BVS_FILE_FORMAT + '\n\
      3. Fill up the first row with ' + STANDARD_TICKER + ' and ' + STANDARD_BVS + '\n\
      4. Retry this command' \
    )

def prepare_data_for_graph(data):
  PBV = 'PBV'

  data[STANDARD_DATE] = pd.to_datetime(data[STANDARD_DATE])
  data[PBV] = data[STANDARD_CLOSE] / data[STANDARD_BVS]
  fig, ax = plt.subplots(3, sharex=True)
  plt.subplots_adjust(hspace=0.5)
  
  ax[0].plot(data[STANDARD_DATE], data[STANDARD_CLOSE])
  ax[0].set_title(STANDARD_CLOSE)
  ax[0].tick_params(axis='both', which='major', labelsize=8)
  ax[0].yaxis.set_major_locator(plt.MaxNLocator(5))
  ax[0].grid()
  
  ax[1].plot(data[STANDARD_DATE], data[STANDARD_BVS])
  ax[1].set_title(STANDARD_BVS)
  ax[1].tick_params(axis='both', which='major', labelsize=8)
  ax[1].yaxis.set_major_locator(plt.MaxNLocator(5))
  ax[1].grid()
  
  ax[2].plot(data[STANDARD_DATE], data[PBV])
  ax[2].set_title(PBV)
  ax[2].tick_params(axis='both', which='major', labelsize=8)
  ax[2].yaxis.set_major_locator(plt.MaxNLocator(5))
  ax[2].grid()

  return plt

def plot_interactive_graph(ticker):
  try:
    data = pd.read_csv(FINAL_FILE_DIR + '/' + ticker.lower() + FINAL_FILE_EXT)
    plt = prepare_data_for_graph(data)
    plt.show()
  except FileNotFoundError:
    print('The data for ticker ' + ticker + ' not found! Please check ' + FINAL_FILE_DIR + '/' + ticker.lower() + FINAL_FILE_EXT)

def plot_graph():
  for filename in os.listdir(FINAL_FILE_DIR):
    if filename.endswith(FINAL_FILE_EXT):
      data = pd.read_csv(FINAL_FILE_DIR + '/' + filename)
      plt = prepare_data_for_graph(data)
      plt.savefig(IMAGE_DIR + '/' + filename[:-len(FINAL_FILE_EXT)] + IMAGE_EXT)
    else:
      continue

def backup_data():
  src_files = os.listdir(FINAL_FILE_DIR)
  for file_name in src_files:
    full_file_name = os.path.join(FINAL_FILE_DIR, file_name)
    if os.path.isfile(full_file_name):
      shutil.copy(full_file_name, BACKUP_DIR)

def offer_replot_graph():
  command = input('Do you want to replot all graphs? It will take some time...\n \
    1. Yes\n \
    2. No\n \
    ')
  
  if (command == '1'):
    plot_graph()
  elif(command == '2'):
    pass
  else:
    print('Command invalid! Please enter one of the command numbers!')

command = input('What do you want to do? Press one of the numbers to execute commands\n \
    1. Input daily stock price \n \
    2. Update BVS\n \
    3. Plot All Graphs\n \
    4. Generate an interactive graph for a company\n \
    5. Exit\n \
  ')

backup_data()
if (command == '1'):
  start = time.time()
  update_daily_price()
  offer_replot_graph()
  end = time.time()
  print('process completed in ' + str(end-start) + 'sec')
elif (command == '2'):
  start = time.time()
  update_bvs()
  offer_replot_graph()
  end = time.time()
  print('process completed in ' + str(end-start) + 'sec')
elif (command == '3'):
  start = time.time()
  plot_graph()
  end = time.time()
  print('process completed in ' + str(end-start) + 'sec')
elif (command == '4'):
  command = input('Which company do you want to see? Enter the ticker!')
  plot_interactive_graph(command)
elif (command == '5'):
  print('Exit...')
else:
  print('Command invalid! Please enter one of the command numbers! Exiting')
