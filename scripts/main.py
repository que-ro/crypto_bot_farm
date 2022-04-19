# import importlib, sys
# importlib.reload(sys.modules['data_accumulator'])


# Backtest the model
# If it looks promising, start building the trade bot

# backtest simulator:
# use describer to get info of 15h previous (+add col one_trade_gain_loss)
# use model to predict which are good or not
# divide volume_quote by nb of predicted good
# use strat on next 45h for each of the predicted currency pair
# see if you have more gains than loss

####
#Machine learning process on regression (with gain_loss_percentage)
#####

