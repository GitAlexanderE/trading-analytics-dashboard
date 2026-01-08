# Trading Dashboard – Full Stack Web Application

This project is a full-stack trading dashboard that processes, analyzes, and visualizes trading data from MetaTrader 5.

The backend is built with Django and Python, using a MySQL database for data storage.
The frontend is implemented with HTML, CSS, JavaScript, and Bootstrap.

## Project Structure

-  `overview/ ` – main Django app containing views, models, templates, and static files  
-  `Website/ ` – Django project configuration (settings, urls, wsgi, etc.)  
-  `mt5_data_import/ ` – script for retrieving and processing MetaTrader 5 data    
-  `manage.py` – Django management script

## Tech Stack

- **Backend:** Python, Django
- **Database:** MySQL
- **Frontend:** HTML, CSS, JavaScript, Bootstrap
- **Data Source:** MetaTrader 5

## Features

- Trading performance analysis (win rate, profit, sessions, weekdays)
- Interactive statistics dashboard
- Clean, responsive, and user-friendly interface
- Structured backend using Django ORM and aggregated performance statistics

## How It Works

1. Trading data is retrieved from MetaTrader 5 and structured for further analysis
2. The data is processed and persisted in a MySQL database using Django ORM
3. Key performance metrics (win rate, profit, sessions, weekdays) are calculated on the backend
4. The results are visualized in a responsive web dashboard for clear and intuitive analysis

## Motivation

This project was developed to strengthen my full-stack development skills and to demonstrate my approach to data-driven web applications in the context of trading analytics.




