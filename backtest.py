import pandas as pd
import pandas_ta as ta
import json
import numpy as np
import datetime as dt
import plotly.graph_objects as go
import pandas as pd
import os
import plotly.io as pio

#####################################################################

#initiate variables
backtest_start_date = input('Enter backtest start date [default: "2019-01-01"] : ') or "2019-01-01"
backtest_end_date = input('Enter backtest end date [default: "2022-12-30"] : ') or "2022-12-30"

start_time = "09:20:00"
end_time = "15:15:00"

retry_count = 10
avwap_period = input('Enter the period of AVWAP indicator("W" for weekly [default] and "M" for Monthly : ') or "W" # "W" for Weekly and "M" for Monthly

sl = float(input('Enter SL value [default: 0.1] : ')) or float(0.1)
tgt = float(input('Enter TGT value [default: 0.1] : ')) or float(0.1)

all_trades = []
moneyness_dict = {"ATM-5" : -5, "ATM-4" : -4,"ATM-3" : -3, "ATM-2" : -2, "ATM-1" : -1, "ATM" : 0, "ATM+1" : 1, "ATM+2" : 2, "ATM+3" : 3, "ATM+4" : 4, "ATM+5" : 5}

selected_moneyness = input('Select Moneyness of Option [default: "ATM"] : ') or "ATM"

result_folder_name = f"results/BN_{avwap_period}_{selected_moneyness}_SL_{sl}_TGT_{tgt}_{backtest_start_date}_to_{backtest_end_date}"
os.makedirs(result_folder_name)

#####################################################################

#import banknifty futures data and pre-process
df_bnf = pd.read_csv("BNF-FUT-WITH-EXPIRY-DATES.csv")

df_bnf = df_bnf[(df_bnf["Date"] >= backtest_start_date) & (df_bnf["Date"] <= backtest_end_date)]

df_bnf["Datetime_DT"] = df_bnf["Datetime_DT"].apply(lambda x: dt.datetime.strptime(x,"%Y-%m-%d %H:%M:%S"))
df_bnf = df_bnf.set_index("Datetime_DT")

#create AVWAP indicator
df_bnf["AVWAP"] = ta.vwap(df_bnf["High"],df_bnf["Low"],df_bnf["Close"],df_bnf["Volume"], anchor = avwap_period)
df_bnf["Prev Close"] = df_bnf["Close"].shift(1)

#create a list of all exxpiry dates
expiry_date_list = ['31JAN19','10JAN19','03JAN19','17JAN19','28FEB19','24JAN19','02JAN20','09JAN20','30JAN20','16JAN20','27FEB20','23JAN20','07JAN21','14JAN21','28JAN21','25FEB21','21JAN21','25MAR21','18FEB21','07FEB19','14FEB19','28MAR19','25APR19','21FEB19','06FEB20','13FEB20','26MAR20','30APR20','20FEB20','11FEB21','04FEB21','04MAR21','01APR21','18MAR21','10FEB22','17FEB22','03FEB22','24FEB22','28APR22','31MAR22','03MAR22','24MAR22','10MAR22','07MAR19','14MAR19','30MAY19','20MAR19','04APR19','10MAR21','29APR21','22APR21','27MAY21','11APR19','18APR19','27JUN19','01APR20','09APR20','16APR20','28MAY20','23APR20','08APR21','15APR21','24JUN21','06MAY21','07APR22','13APR22','30JUN22','26MAY22','21APR22','05MAY22','29DEC22','04JUN20','25JUN20','11JUN20','30JUL20','03JUN21','29JUL21','10JUN21','17JUN21','26AUG21','15JUL21','01JUL21','02JUN22','09JUN22','16JUN22','28JUL22','23JUN22','25AUG22','29SEP22','04JUL19','25JUL19','11JUL19','29AUG19','09JUL20','02JUL20','27AUG20','16JUL20','23JUL20','08JUL21','22JUL21','30SEP21','07JUL22','14JUL22','21JUL22','04AUG22','08AUG19','01AUG19','14AUG19','26SEP19','31OCT19','11AUG22','18AUG22','01SEP22','27OCT22','03SEP20','24SEP20','29OCT20','10SEP20','17SEP20','26NOV20','02SEP21','09SEP21','16SEP21','28OCT21','25NOV21','23SEP21','30DEC21','08SEP22','15SEP22','22SEP22','24NOV22','03OCT19','10OCT19','28NOV19','17OCT19','26DEC19','24OCT19','07NOV19','01OCT20','15OCT20','08OCT20','22OCT20','14OCT21','07OCT21','21OCT21','03NOV21','11NOV21','14NOV19','21NOV19','18NOV21','16DEC21','09DEC21','02DEC21','27JAN22','01DEC22','10NOV22','03NOV22','17NOV22','25JAN23','30MAR23','31DEC20','10DEC20','03DEC20','24DEC20','17DEC20','23DEC21','08DEC22','22DEC22','15DEC22','23FEB23','29JUN23','05MAR20','12MAR20','19MAR20','17MAR22','02MAY19','09MAY19','16MAY19','23MAY19','12MAY22','19MAY22','18JUN20','18JUL19','05SEP19','05AUG21','12AUG21','18AUG21','06OCT22','05NOV20','12NOV20','19NOV20','05DEC19','12DEC19','19DEC19','20JAN22','05JAN23','13JAN22','06JAN22','20MAY21','12MAY21','06JUN19','13JUN19','20JUN19','06AUG20','13AUG20','20AUG20','12SEP19','19SEP19','13OCT22','20OCT22','07MAY20','14MAY20','21MAY20','22AUG19','28SEP23','12JAN23','19JAN23','29MAR23','02FEB23']
expiry_date_list_DT = []
for i in expiry_date_list:
    expiry_date_list_DT.append(dt.datetime.strptime(i,"%d%b%y").date())
    
#####################################################################

#function to find nearest expiry
def find_nearest_expiry(date_string):
    
    date = dt.datetime.strptime(date_string, '%Y-%m-%d').date()
    nearest_expiry = min(expiry_date_list_DT, key=lambda x: abs(x - date) if x >= date else dt.timedelta.max)
    
    nearest_expiry = nearest_expiry.strftime("%d%b%y").upper()
    
    return nearest_expiry

#function to find option strike symbol
def find_option_strike(fut_close, factor, expiry_date_str ,option_type):
    
    strike = str(round(fut_close/100)*100 + 100*factor)
    option_strike = "BANKNIFTY" + expiry_date_str + strike + option_type + ".NFO"
    
    return option_strike

#function to find the ohlc of option strike
def find_option_strike_ohlc(df_option, option_strike, datetime_str, retry_count):
    
    if retry_count > 0:
        
        try:
            ohlc = df_option[(df_option["Ticker"] == option_strike) & (df_option["Datetime"] == datetime_str)].iloc[-1]
        
        except:
            retry_count -= 1
            print(f'No data found for {datetime_str} candle. Checking the previous candle')
            datetime_str = (dt.datetime.strptime(datetime_str,"%Y-%m-%d %H:%M:%S") - dt.timedelta(minutes=1)).strftime("%Y-%m-%d %H:%M:%S")
            
            ohlc = find_option_strike_ohlc(df_option, option_strike, datetime_str, retry_count)
            
        return ohlc
    
    else:
        return -1

#function to reset the trade details
def reset_trade():
    trade_dict = {}
    trade_dict["status"] = "NO TRADE"
    return trade_dict
    
#function to simulate the trades on daily basis
def trade_simulator(df_bn, moneyness):
    
    intraday_trades = []
    trade_dict = reset_trade()
    
    datetime_str = df_bn["Datetime"].iloc[-1]
    yyyy = datetime_str[:4]
    mm = datetime_str[5:7]
    dd = datetime_str[8:10]
    date_str = dd + mm + yyyy
    
    df_option = pd.read_csv(f"data_refined/GFDLNFO_BACKADJUSTED_" + date_str + ".csv")

    for i in range(df_bn.shape[0]):
        
        ohlc = df_bn.iloc[i]
        prev_ohlc = df_bn.iloc[i-2:i][["Open","High","Low","Close"]].values.tolist()
        prev_ohlc_list = [item for sublist in prev_ohlc for item in sublist]
        
        close_value = ohlc["Close"]
        prev_close_value = ohlc["Prev Close"]
        avwap_value = ohlc["AVWAP"]
        ohlc_time = ohlc["Time"]
        
        #take trades if there are no open positions
        if trade_dict["status"] == "NO TRADE" and ohlc_time >= start_time and ohlc_time <= end_time:
            
            if all(avwap_value > num for num in prev_ohlc_list) and close_value > avwap_value:
                
                print(f'Prev Close: {prev_close_value}\nAVWAP: {avwap_value}\n Close: {close_value}')
                
                try:
                    trade_dict["entry_time"] = ohlc["Datetime"]
                    trade_dict["trade_type"] = "LONG"
                    trade_dict["option_type"] = "CE"
                    trade_dict["moneyness"] = moneyness
                    trade_dict["strike"] = find_option_strike(close_value,moneyness_dict[moneyness],ohlc["Nearest Weekly Expiry date"],"CE") #negative value for moneyness as it is CE option
                    trade_dict["entry_price"] = find_option_strike_ohlc(df_option, trade_dict["strike"],trade_dict["entry_time"], retry_count)["Close"]
                    trade_dict["sl_price"] = round(trade_dict["entry_price"]*(1 - sl),2)
                    trade_dict["tgt_price"] = round(trade_dict["entry_price"]*(1 + tgt),2)
                    trade_dict["status"] = "OPEN"
                    
                    print(f'BUY {trade_dict["strike"]} at {trade_dict["entry_price"]} at {trade_dict["entry_time"]}')
                
                except Exception as e:
                    print(e)
                    print("Entry Issue")
                    trade_dict = reset_trade()
                    continue
            
            # elif prev_close_value > avwap_w_value and close_value < avwap_w_value:
            elif all(avwap_value < num for num in prev_ohlc_list) and close_value < avwap_value:
                
                print(f'Prev Close: {prev_close_value}\nAVWAP: {avwap_value}\n Close: {close_value}')
                
                try:
                    trade_dict["entry_time"] = ohlc["Datetime"]
                    trade_dict["trade_type"] = "LONG"
                    trade_dict["option_type"] = "PE"
                    trade_dict["moneyness"] = moneyness
                    trade_dict["strike"] = find_option_strike(close_value,-moneyness_dict[moneyness],ohlc["Nearest Weekly Expiry date"],"PE") #negative value for moneyness as it is PE option
                    trade_dict["entry_price"] = find_option_strike_ohlc(df_option, trade_dict["strike"],trade_dict["entry_time"], retry_count)["Close"]
                    trade_dict["sl_price"] = round(trade_dict["entry_price"]*(1 - sl),2)
                    trade_dict["tgt_price"] = round(trade_dict["entry_price"]*(1 + tgt),2)
                    trade_dict["status"] = "OPEN"

                    print(f'BUY {trade_dict["strike"]} at {trade_dict["entry_price"]} at {trade_dict["entry_time"]}')
                
                except Exception as e:
                    print(e)
                    print("Entry Issue")
                    trade_dict = reset_trade()
                    continue              
            else:
                pass
                #print(f'No open positions at {ohlc["Datetime"]}')
        
        # if there are any open positions check for sl/tgt hit
        elif trade_dict["status"] == "OPEN" and ohlc_time >= start_time and ohlc_time <= end_time:
            
            try:
                ltp_ohlc = find_option_strike_ohlc(df_option, trade_dict["strike"],ohlc["Datetime"], retry_count)
            except Exception as e:
                print(e)
                print("Issue")
                continue
                    
            if ltp_ohlc["Low"] <= trade_dict["sl_price"]:
                
                trade_dict["exit_price"] = trade_dict["sl_price"]
                trade_dict["exit_time"] = ltp_ohlc["Datetime"]
                trade_dict["pnl"] = round(trade_dict["exit_price"] - trade_dict["entry_price"],2)
                trade_dict["status"] = "SL-HIT"
                
                intraday_trades.append(trade_dict)
                
                print(f'SL-HIT {trade_dict["strike"]} at {trade_dict["exit_price"]} at {trade_dict["exit_time"]}')
                trade_dict = reset_trade()

            
            elif ltp_ohlc["High"] >= trade_dict["tgt_price"]:

                trade_dict["exit_price"] = trade_dict["tgt_price"]
                trade_dict["exit_time"] = ltp_ohlc["Datetime"]
                trade_dict["pnl"] = round(trade_dict["exit_price"] - trade_dict["entry_price"],2)
                trade_dict["status"] = "TGT-HIT"
                
                intraday_trades.append(trade_dict)
                
                print(f'TGT-HIT {trade_dict["strike"]} at {trade_dict["exit_price"]} at {trade_dict["exit_time"]}')
                trade_dict = reset_trade()
                
            
            else:
                pass
                #print(f'SL/TGT not hit for {trade_dict["strike"]} at {ohlc["Datetime"]}')
        
        else:
            
            # square off all open trades at 03:15 PM  
            if trade_dict["status"] == "OPEN":
                
                try:
                    ltp_ohlc = find_option_strike_ohlc(df_option, trade_dict["strike"],ohlc["Datetime"], retry_count)
                except Exception as e:
                    print(e)
                    print("Issue")
                    continue
                            
                trade_dict["exit_price"] = ltp_ohlc["Close"]
                trade_dict["exit_time"] = ltp_ohlc["Datetime"]
                trade_dict["pnl"] = round(trade_dict["exit_price"] - trade_dict["entry_price"],2)
                trade_dict["status"] = "TIME-SQ-OFF"
                
                intraday_trades.append(trade_dict)
                
                print(f'TIME-SQ-OFF {trade_dict["strike"]} at {trade_dict["exit_price"]} at {trade_dict["exit_time"]}')
                trade_dict = reset_trade()
            
            else:
                pass
                #print(f'Trades not allowed at {ohlc["Datetime"]}')
    
    return intraday_trades

#####################################################################

# main code

trade_dates = df_bnf["Date"].unique().tolist()

for today_date in trade_dates:
    
    print(f"Simulating Trades on {today_date}")
        
    df_today = df_bnf[df_bnf["Date"] == today_date]
    intraday_trades = trade_simulator(df_today,selected_moneyness)
    all_trades.extend(intraday_trades)
    
results = pd.DataFrame(all_trades)

#####################################################################

#strategy stats calculation and plotting

# Add the 'Cumulative PNL' column
results['Cumulative PNL'] = results['pnl'].cumsum()

# Add the 'Drawdown' column
results['Drawdown'] = results['Cumulative PNL'] - results['Cumulative PNL'].cummax()

# Add the 'Winning Streak' and 'Losing Streak' columns
results['Streak'] = (results['pnl'] > 0).astype(int).diff().ne(0).cumsum()
results['Winning Streak'] = results[results['pnl'] > 0].groupby(results['Streak']).cumcount() + 1
results['Losing Streak'] = results[results['pnl'] <= 0].groupby(results['Streak']).cumcount() + 1
results[['Winning Streak', 'Losing Streak']] = results[['Winning Streak', 'Losing Streak']].fillna(0)

# Convert 'entry_time' to datetime and set it as the index
results['entry_time'] = pd.to_datetime(results['entry_time'])
results.set_index('entry_time', inplace=True)

# calculate strategy stats
total_trades = len(results)
winning_trades = len(results[results['pnl'] > 0])
losing_trades = len(results[results['pnl'] <= 0])
accuracy = round((winning_trades / total_trades)*100,2)
winning_streak = round(results['Winning Streak'].max())
losing_streak = round(results['Losing Streak'].max())
max_profit = results['pnl'].max()
max_loss = results['pnl'].min()
max_drawdown = round(results['Drawdown'].max(),2)
avg_profit_winning_trades = round(results[results['pnl'] > 0]['pnl'].mean(),2)
avg_loss_losing_trades = round(results[results['pnl'] <= 0]['pnl'].mean(),2)
avg_pnl = round(results['pnl'].mean(),2)

# Print the statistics
print(f'Total trades: {total_trades}')
print(f'Winning trades: {winning_trades}')
print(f'Losing trades: {losing_trades}')
print(f'Accuracy: {accuracy} %')
print(f'Winning streak: {winning_streak}')
print(f'Losing streak: {losing_streak}')
print(f'Max profit: {max_profit}')
print(f'Max loss: {max_loss}')
print(f'Max drawdown: {max_drawdown}')
print(f'Average profit on winning trades: {avg_profit_winning_trades}')
print(f'Average loss on losing trades: {avg_loss_losing_trades}')
print(f'Average PNL: {avg_pnl}')

#####################################################################

# save results and stats data in the folder
results.to_csv(f"{result_folder_name}/trade_details.csv")

# Open the file in write mode
with open(f'{result_folder_name}/stats.txt', 'w') as file:
    # Write the data to the file
    file.write(f'Total trades: {total_trades}\n')
    file.write(f'Winning trades: {winning_trades}\n')
    file.write(f'Losing trades: {losing_trades}\n')
    file.write(f'Accuracy: {accuracy} %\n')
    file.write(f'Winning streak: {winning_streak}\n')
    file.write(f'Losing streak: {losing_streak}\n')
    file.write(f'Max profit: {max_profit}\n')
    file.write(f'Max loss: {max_loss}\n')
    file.write(f'Max drawdown: {max_drawdown}\n')
    file.write(f'Average profit on winning trades: {avg_profit_winning_trades}\n')
    file.write(f'Average loss on losing trades: {avg_loss_losing_trades}\n')
    file.write(f'Average PNL: {avg_pnl}\n')

# Create a line plot for 'Cumulative PNL'
fig1 = go.Figure()
fig1.add_trace(go.Scatter(x=results.index.date, y=results['Cumulative PNL'], mode='lines', name='Cumulative PNL'))
fig1.update_layout(title='Cumulative PNL over Time', xaxis_title='Date', yaxis_title='Cumulative PNL')
file_path = os.path.join(result_folder_name, 'equity_curve.png')
pio.write_image(fig1, file_path, format='png')

# Create a line plot for 'Drawdown'
fig2 = go.Figure()
fig2.add_trace(go.Scatter(x=results.index.date, y=results['Drawdown'], mode='lines', name='Drawdown'))
fig2.update_layout(title='Drawdown over Time', xaxis_title='Date', yaxis_title='Drawdown')
file_path = os.path.join(result_folder_name, 'dd_curve.png')
pio.write_image(fig2, file_path, format='png')
