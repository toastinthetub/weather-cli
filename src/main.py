import datetime
import asyncio
import curses
import httpx
import time

# Constants for curses dimensions
HEIGHT, WIDTH = 0, 0
LBH, LBW, LBY, LBX = 0, 0, 0, 0
DBH, DBW, DBY, DBX = 0, 0, 0, 0

current_date = datetime.datetime.now()
formatted_date = current_date.strftime("%m/%d/%Y")

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

httpx_client = httpx.AsyncClient()

WEATHER_API_BASE = 'https://api.open-meteo.com/v1'  # Forecast API base
LOCATION_API_BASE = 'https://www.zipcodeapi.com'   # Geocoding API base
LOCATION_API_KEY = '/3CDPn5fR5eVr33k0VLlC9HO6Vyzh32vCbn5v5l9Dsr4buR4EdPkKuOu3vl3xRcVs'  # da api kee

weather_result = None 
location_data = None

async def get_location(zipcode: int):
    global location_data
    url = f"{LOCATION_API_BASE}/rest{LOCATION_API_KEY}/info.json/{zipcode}/degrees"

    location_response = await httpx_client.get(url)
    location_data = location_response.json()
    return location_data


async def get_forecast(lat: float, lon: float):
    global weather_result
    url = f"{WEATHER_API_BASE}/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": ["temperature_2m", "relative_humidity_2m", "rain", "snowfall", "pressure_msl", "visibility"],
        "timezone": "PST",
    }

    weather_response = await httpx_client.get(url, params=params)
    weather_result = weather_response.json()
    return weather_result


async def get_user_input(stdscr, prompt):

    HEIGHT, WIDTH = stdscr.getmaxyx()

    LBH = 3  # Loading box height
    LBW = 40  # Loading box width
    LBY = (HEIGHT - LBH) // 2  # Loading box y param (center on y)
    LBX = (WIDTH - LBW) // 2  # Loading box x param (center on x)

    IWIN = curses.newwin(LBH, LBW, LBY, LBX)
    IWIN.box()
    IWIN.addstr(1, 1, prompt)
    IWIN.refresh()

    curses.curs_set(1)
    IWIN.keypad(True)

    curses.echo()
    user_input = IWIN.getstr(1, len(prompt) + 1, 30)

    curses.curs_set(0)
    IWIN.keypad(False)
    curses.noecho()

    return user_input.decode('utf-8')  # not sure why i bave to do this but i do so


def parse_location_dat(location_data):
    city = location_data['city']
    state = location_data['state']
    timezone_id = location_data['timezone']['timezone_identifier']
    timezone_ab = location_data['timezone']['timezone_abbr']
    utc_off = location_data['timezone']['utc_offset_sec']
    area_codes = location_data['area_codes']

    return {
        'city': city,
        'state': state,
        'timezone_id': timezone_id,
        'timezone_abbr': timezone_ab,
        'utc_offset_sec': utc_off,
        'area_codes': area_codes
    }


def parse_todays_weather(weather_result):
    useful_time_vals = [
        "0000", "0100", "0200", "0300", "0400", "0500",
        "0600", "0700", "0800", "0900", "1000", "1100",
        "1200", "1300", "1400", "1500", "1600", "1700",
        "1800", "1900", "2000", "2100", "2200", "2300",
    ]

    time_vals = weather_result['hourly']['time']  # Parse time
    temp_vals = weather_result['hourly']['temperature_2m']  # Parse temp
    hum_vals = weather_result['hourly']['relative_humidity_2m']  # Parse humidity
    rain_vals = weather_result['hourly']['rain']  # Parse rain
    pres_vals = weather_result['hourly']['pressure_msl']  # Parse pressure
    snowf_vals = weather_result['hourly']['snowfall']  # Parse snowfall
    vis_vals = weather_result['hourly']['visibility']  # Parse visbility

    num_entries = min(24, len(time_vals))
    weather_data = []

    for i in range(num_entries):
        weather_data.append((useful_time_vals[i], temp_vals[i], hum_vals[i], rain_vals[i], snowf_vals[i], pres_vals[i], vis_vals[i]))

    return weather_data

def parse_next_weather(weather_result):
    print("This isn't ready yet")


def draw_sect(stdscr, name, h, w, y, x, str=None, stry=None, strx=None):
    name_win = curses.newwin(h, w, y, x)
    name_win.box()
    if str is not None and stry is not None and strx is not None:
        name_win.addstr(stry, strx, f"{str}", curses.A_BOLD)
    name_win.refresh()

    return name_win

def draw_loading_box(stdscr, str):
    # create loading box, data for it is created within in the function
    HEIGHT, WIDTH = stdscr.getmaxyx()
    LBH = 3  # Loading box height
    LBW = 40  # Loading box width
    LBY = (HEIGHT - LBH) // 2  # Loading box y param (center on y)
    LBX = (WIDTH - LBW) // 2  # Loading box x param (center on x)

    loading_box = curses.newwin(LBH, LBW, LBY, LBX)
    loading_box.box()
    loading_box.addstr(1, 2, f"{str}")
    loading_box.refresh()

    return loading_box

def draw_heading_box(stdscr, weather_usable, location_usable):
    
    HEIGHT, WIDTH = stdscr.getmaxyx()

    HBH = 3
    HBW = WIDTH - 1
    HBY = 0
    HBX = 0

    head_win = curses.newwin(HBH, HBW, HBY, HBX)
    head_win.box()
    head_win.addstr(1, 2, f"WEATHER FOR {formatted_date} IN {location_usable['city']}, {location_usable['state']}.", curses.A_BOLD)
    head_win.refresh()

    return head_win

def draw_data_box(stdscr, weather_usable):

    HEIGHT, WIDTH = stdscr.getmaxyx()

    DBH = (HEIGHT//2) - 3 # Data box height
    DBW = (WIDTH//3) + (WIDTH//3)  # Data box width
    DBY = (HEIGHT - DBH) // 2  # Data box y param (center...?)
    DBX = (WIDTH - DBW) // 2  # Data box x param (center...?)

    header_spacers = DBW // 7  # Calculate the width of each header column

    data_win = curses.newwin(DBH, DBW, 3, 0)
    data_win.box()
    headers = ["Time", "Temp (C)", "Humidity", "Rainfall", "Snowfall", "Pressure", "Visibility"]
    row_format = "{:<{header_width}}" * len(headers)  # Use '<' for left alignment
    for i, header in enumerate(headers):
        data_win.addstr(1, i * header_spacers + 2, header, curses.A_BOLD)  # Add headers one row down
    for i, row in enumerate(weather_usable, start=2):  # Start adding data from the second row
        for j, item in enumerate(row):
            data_win.addstr(i, j * header_spacers + 2, str(item))  # Add data
    data_win.refresh()

    return data_win

def draw_general_box(stdscr, weather_usable, location_usable):

    HEIGHT, WIDTH = stdscr.getmaxyx()

    GBH = (HEIGHT//2) - 3
    GBW = (WIDTH//3)
    GBY = 3
    GBX = (WIDTH//3) + (WIDTH//3)

    GIB = curses.newwin(GBH, GBW, GBY, GBX)
    GIB.box()

    GIB.addstr(1, 2, f"Current Date and Time: {current_date.strftime('%d/%m/%Y %H:%M')}")
    GIB.addstr(3, 2, f"City: {location_usable['city']}")
    GIB.addstr(4, 2, f"State: {location_usable['state']}")
    GIB.addstr(5, 2, f"Latitude: {location_data['lat']}")
    GIB.addstr(6, 2, f"Longitude: {location_data['lng']}")

    GIB.refresh()

    return GIB

def draw_error_box(stdscr):
    
    HEIGHT, WIDTH = stdscr.getmaxyx()

    EBH = 3  # Loading box height
    EBW = 40  # Loading box width
    EBY = (HEIGHT - EBH) // 2  # Loading box y param (center on y)
    EBX = (WIDTH - EBW) // 2  # Loading box x param (center on x)

    ERB = curses.newwin(EBH, EBW, EBY, EBX)
    ERB.box()
    ERB.addstr(1, 2, "TERMINAL SIZE TOO SMALL.")
    ERB.refresh()

    return ERB

def draw_db1(stdscr, weather_usable):

    HEIGHT, WIDTH = stdscr.getmaxyx()

    DB1H = (HEIGHT//4)
    DB1W = (WIDTH//3)
    DB1Y = (HEIGHT//2)
    DB1X = 0

    DB1 = curses.newwin(DB1H, DB1W, DB1Y, DB1X)
    DB1.box()
    DB1.refresh()

    return DB1

def draw_db2(stdscr, weather_usable):

    HEIGHT, WIDTH = stdscr.getmaxyx()

    DB2H = (HEIGHT//4)
    DB2W = (WIDTH//3)
    DB2Y = (HEIGHT//2)
    DB2X = (WIDTH//3)

    DB2 = curses.newwin(DB2H, DB2W, DB2Y, DB2X)
    DB2.box()
    DB2.refresh()

    return DB2

def draw_db3(stdscr, weather_usable):

    HEIGHT, WIDTH = stdscr.getmaxyx()

    DB3H = (HEIGHT//4)
    DB3W = (WIDTH//3)
    DB3Y = (HEIGHT//2)
    DB3X = (WIDTH//3) + (WIDTH//3)

    DB3 = curses.newwin(DB3H, DB3W, DB3Y, DB3X)
    DB3.box()
    DB3.refresh()

    return DB3

def draw_db4(stdscr, weather_usable):

    HEIGHT, WIDTH = stdscr.getmaxyx()

    DB4H = (HEIGHT//4)
    DB4W = (WIDTH//3)
    DB4Y = (HEIGHT //2) + (HEIGHT//4)
    DB4X = 0

    DB4 = curses.newwin(DB4H, DB4W, DB4Y, DB4X)
    DB4.box()
    DB4.refresh()

    return DB4

def draw_db5(stdscr, weather_usable):

    HEIGHT, WIDTH = stdscr.getmaxyx()

    DB5H = (HEIGHT//4)
    DB5W = (WIDTH//3)
    DB5Y = (HEIGHT //2) + (HEIGHT//4)
    DB5X = (WIDTH//3)

    DB5 = curses.newwin(DB5H, DB5W, DB5Y, DB5X)
    DB5.box()
    DB5.refresh()

    return DB5

def draw_db6(stdscr, weather_usable):

    HEIGHT, WIDTH = stdscr.getmaxyx()

    DB6H = (HEIGHT//4)
    DB6W = (WIDTH//3)
    DB6Y = (HEIGHT //2) + (HEIGHT//4)
    DB6X = (WIDTH//3) + (WIDTH//3)

    DB6 = curses.newwin(DB6H, DB6W, DB6Y, DB6X)
    DB6.box()
    DB6.refresh()

    return DB6

async def main(stdscr):
    # init curses bs
    HEIGHT, WIDTH = stdscr.getmaxyx()
    curses.curs_set(0)
    stdscr.clear()

    user_input = await get_user_input(stdscr, "ENTER YOUR ZIPCODE:") # user in for zipcode
    loop.create_task(get_location(user_input))

    load_loc_box = draw_loading_box(stdscr, "LOADING LOCATION...")

    while location_data is None:
        await asyncio.sleep(0.02)

    loaded_loc_box = draw_loading_box(stdscr, "LOCATION FOUND.")
    await asyncio.sleep(0.5)

    lat = location_data['lat']
    lon = location_data['lng']
    loop.create_task(get_forecast(lat, lon))

    load_wea_box = draw_loading_box(stdscr, "LOADING FORECAST...")

    while weather_result is None:
        await asyncio.sleep(0.02)

    loaded_wea_box = draw_loading_box(stdscr, "FORECAST FOUND.")
    await asyncio.sleep(0.5)

    stdscr.clear()
    stdscr.refresh()

    # parse da loco parse da weadah
    location_usable = parse_location_dat(location_data)
    weather_usable = parse_todays_weather(weather_result)

    header_win = draw_heading_box(stdscr, weather_usable, location_usable)
    data_win = draw_data_box(stdscr, weather_usable=weather_usable)
    general_win = draw_general_box(stdscr, weather_usable=weather_usable, location_usable=location_usable)

    data_box_one = draw_db1(stdscr, weather_usable)
    data_box_two = draw_db2(stdscr, weather_usable)
    data_box_three = draw_db3(stdscr, weather_usable)
    data_box_four = draw_db4(stdscr, weather_usable)
    data_box_five = draw_db5(stdscr, weather_usable)
    data_box_six = draw_db6(stdscr, weather_usable)

    while True:

        HEIGHT, WIDTH = stdscr.getmaxyx()

        key = data_win.getch()
        if key == ord('q'):
            break

        if HEIGHT <= 55 or WIDTH <= 136: # check if screen size is too small
                stdscr.clear()
                stdscr.refresh()
                error_box = draw_error_box(stdscr)
                HEIGHT, WIDTH = stdscr.getmaxyx()

        else:
            
            HEIGHT, WIDTH = stdscr.getmaxyx()
            stdscr.clear()
            stdscr.refresh()

            location_usable = parse_location_dat(location_data)
            weather_usable = parse_todays_weather(weather_result)

            header_win = draw_heading_box(stdscr, weather_usable, location_usable)
            data_win = draw_data_box(stdscr, weather_usable=weather_usable)
            general_win = draw_general_box(stdscr, weather_usable=weather_usable, location_usable=location_usable)

            data_box_one = draw_db1(stdscr, weather_usable)
            data_box_two = draw_db2(stdscr, weather_usable)
            data_box_three = draw_db3(stdscr, weather_usable)
            data_box_four = draw_db4(stdscr, weather_usable)
            data_box_five = draw_db5(stdscr, weather_usable)
            data_box_six = draw_db6(stdscr, weather_usable)                

if __name__ == "__main__":
    curses.wrapper(lambda stdscr: loop.run_until_complete(main(stdscr)))
    loop.close()
