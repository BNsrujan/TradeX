from flask import Flask
from routes import doonchian_channel,consecutive_candles,vcp,Bollinger_bands,darvas_box, morning_evening_star, zones, faq, help, news, auth, data, home, support_resistance, trend_lines, inside_bars, double_bottom, double_top, v_shape_patterns, head_and_shoulders, cup_and_handle, ema_series, analysis, triangles, submit ,psych, contactus, aboutus ,educationresorce, beginersguide, topindicators, technicalanalysis, stocktradingpattern, Riskmanagement, optiontradingindia, optiontrading, marketinsights, intradaytradingtips, optiontrading, Discipline
from datetime import date
from time import sleep
import os
import sys
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import pandas as pd
from bs4 import BeautifulSoup
from flask import Flask, render_template
import requests
import pandas as pd
import mysql.connector
from mysql.connector import Error
from datetime import datetime
from dateutil.relativedelta import relativedelta
import plotly.graph_objects as go
import numpy as np
from plotly.subplots import make_subplots
from sklearn.cluster import KMeans
from scipy.signal import argrelextrema
# import pandas_ta as ta
import plotly.io as pio
from sklearn.cluster import DBSCAN
import json
from fyers_apiv3 import fyersModel
import datetime as dt
import plotly
import pyotp
import mysql.connector
from urllib.parse import parse_qs, urlparse
import base64
import warnings
from math import atan2, degrees, sqrt
import pytz
import math
import requests
from time import sleep
from datetime import datetime, timedelta, date
import webbrowser
import os
import sys
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
# from flask_mail import Mail, Message
import pandas as pd
import plotly.graph_objects as go
import numpy as np
from plotly.subplots import make_subplots
from sklearn.cluster import KMeans
# import pandas_ta as ta
import plotly.io as pio
from sklearn.linear_model import LinearRegression
import json
from fyers_apiv3 import fyersModel
import os
import datetime as dt
import plotly
import pyotp
import mysql.connector
import csv


app = Flask(__name__)
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'
users = {'admin': {'password': 'user98440', 'role': 'admin'},
         'user2': {'password': 'user98840', 'role': 'limited'},
         'user1': {'password': 'user@123', 'role': 'admin'}
         }

# Register Blueprints

app.register_blueprint(news.bp)
app.register_blueprint(analysis.bp)
app.register_blueprint(faq.bp)
app.register_blueprint(help.bp)
app.register_blueprint(auth.bp)
app.register_blueprint(data.bp)
app.register_blueprint(home.bp)
app.register_blueprint(support_resistance.bp)  # New blueprint
app.register_blueprint(trend_lines.bp)          # New blueprint
app.register_blueprint(inside_bars.bp)           # New blueprint
app.register_blueprint(double_top.bp)
app.register_blueprint(double_bottom.bp)
app.register_blueprint(v_shape_patterns.bp)
app.register_blueprint(head_and_shoulders.bp)
app.register_blueprint(cup_and_handle.bp)
app.register_blueprint(ema_series.bp)
app.register_blueprint(zones.bp)
app.register_blueprint(morning_evening_star.bp)
app.register_blueprint(darvas_box.bp)
app.register_blueprint(Bollinger_bands.bp)
app.register_blueprint(vcp.bp)
app.register_blueprint(consecutive_candles.bp)
app.register_blueprint(doonchian_channel.bp)
app.register_blueprint(triangles.bp)
app.register_blueprint(submit.bp)
app.register_blueprint(psych.bp)
app.register_blueprint(contactus.bp)
app.register_blueprint(aboutus.bp)
app.register_blueprint(educationresorce.bp)
app.register_blueprint(beginersguide.bp)
app.register_blueprint(topindicators.bp)
app.register_blueprint(technicalanalysis.bp)
app.register_blueprint(stocktradingpattern.bp)
app.register_blueprint(Riskmanagement.bp)
app.register_blueprint(optiontradingindia.bp)
app.register_blueprint(optiontrading.bp)
app.register_blueprint(marketinsights.bp)
app.register_blueprint(intradaytradingtips.bp)
app.register_blueprint(Discipline.bp)




application = app.wsgi_app

if __name__ == '__main__':
    app.run(debug=True, use_reloader=True)

