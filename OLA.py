import pandas as pd
import streamlit as st
from PIL import Image
from streamlit_option_menu import option_menu
import sqlitecloud
from datetime import datetime, date, time

# ======= SQLite Cloud Connection =======

connection = sqlitecloud.connect("sqlitecloud://cerkhyoadz.g3.sqlite.cloud:8860/OlaRideInsight?apikey=tHmbijkoca6HjBt8SwnTjowXbOJfZnabnbuTJLjVaW4")


# ================= SAFE QUERY FUNCTION =================
def run_query(query):
    cur = connection.cursor()
    cur.execute(query)
    rows = cur.fetchall()

    if cur.description:
        cols = [d[0] for d in cur.description]
        return pd.DataFrame(rows, columns=cols)
    else:
        return pd.DataFrame(rows)

def run_scalar(query):
    cur = connection.cursor()
    cur.execute(query)
    return cur.fetchone()[0]


# ================= INITIAL CHECK =================
record_count = run_scalar("SELECT COUNT(*) FROM ola_bookings")
expected_rows = 103024

if record_count < expected_rows:
    # =========== Read Excel File =========
    path = r"OLA_DataSet.xlsx"
    df = pd.read_excel(path)

    df["Date"] = df["Date"].astype(str)
    df["Time"] = df["Time"].astype(str)

    # ======= DATA CLEANING ========

    # Fill cancellation-related columns
    cols = [
        'Canceled_Rides_by_Customer',
        'Canceled_Rides_by_Driver',
        'Incomplete_Rides',
        'Incomplete_Rides_Reason'
    ]
    df[cols] = df[cols].fillna('Not Applicable')

    # Fill Payment Method
    df['Payment_Method'] = df['Payment_Method'].fillna('Unknown')

    # Fill Numeric Columns
    numeric_cols = [    
        'V_TAT',
        'C_TAT',
        'Driver_Ratings',
        'Customer_Rating'
    ]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')
        median_value = df[col].median()
        df[col] = df[col].fillna(median_value)

    # ========= Save Cleaned CSV =========
    df.to_csv("ola_bookings_cleaned.csv", index=False)


    # ====  Convert NaN to None  =====
    df = df.where(pd.notnull(df), None)

    # ========= Convert ALL Timestamp values to String =========
    
    for col in df.columns:
        df[col] = df[col].apply(
            lambda x: str(x)
            if isinstance(x, (pd.Timestamp, datetime, date, time))
            else x
        )
  
    # ========= Check for Remaining Timestamp Values =========
    for col in df.columns:
        if df[col].apply(lambda x: isinstance(x, pd.Timestamp)).any():
            print(f"Timestamp still exists in column: {col}")

    # ========= Prepare Data =========
    data = df.values.tolist()   

    found = False

    for row in data:
        for value in row:
            if isinstance(value, (datetime, date, time, pd.Timestamp)):
                print("Still Found:", type(value), value)
                found = True

    if not found:
        print("All date/time values converted successfully.")

    data = [tuple(row) for row in df.values.tolist()]

    # ======= Insert into table ========
    insert_query = """
    INSERT OR IGNORE INTO ola_bookings(
        Date,
        Time,
        Booking_ID,
        Booking_Status,
        Customer_ID,
        Vehicle_Type,
        Pickup_Location,
        Drop_Location,
        V_TAT,
        C_TAT,
        Canceled_Rides_by_Customer,
        Canceled_Rides_by_Driver,
        Incomplete_Rides,
        Incomplete_Rides_Reason,
        Booking_Value,
        Payment_Method,
        Ride_Distance,
        Driver_Ratings,
        Customer_Rating,
        Vehicle_Images
    )
    VALUES (
        ?, ?, ?, ?, ?,
        ?, ?, ?, ?, ?,
        ?, ?, ?, ?, ?,
        ?, ?, ?, ?, ?
    )
    """
    # ========= Insert Data =========
    data = [tuple(x) for x in df.values.tolist()]
    batch_size = 5000

    for i in range(0, len(data), batch_size):
        batch = data[i:i + batch_size]
        cur = connection.cursor()
        cur.executemany(insert_query, batch)
        connection.commit()
        print(f"Inserted {min(i + batch_size, len(data))} / {len(data)} rows")
 

#======= Streamlit Page Design ==========

st.title('**OLA RIDE INSIGHTS**')
img = Image.open("OLA_LOGO.png")
st.image(img,  width=350 )

with st.sidebar:
    selected = option_menu(
        "INSIGHTS",
        ["Home", "Successful Bookings", "Average Ride Distance", "Cancelled Rides", "Customers With Highest Ride Cancellation", "Rides Cancelled by Drivers", "Driver's Rating", "UPI Rides", "Average Customer Rating", "Total booking value", "Incomplete Rides"],
        default_index=0
    )

if selected == "Home":
    st.text(" ")
    st.text("OLA, a leading ride-hailing service, generates vast amounts of data related to ride bookings, driver availability, fare calculations, and customer preferences. To enhance operational efficiency, improve customer satisfaction, and optimize business strategies, this project focuses on analyzing OLA’s ride-sharing data.")
    st.text("The project will involve cleaning and processing raw ride data, performing exploratory data analysis (EDA), developing a dynamic Power BI dashboard, and creating a Streamlit-based web application to present key findings in an interactive and user-friendly manner.")

elif selected == "Successful Bookings":
    st.subheader("RETRIEVE ALL SUCCESSFUL BOOKINGS")
    st.text(
        "This section displays all ride bookings that were completed successfully. "
        "Analyzing successful bookings helps identify ride demand, customer usage patterns,revenue trends, and overall operational performance.")

    # Get total number of successful bookings
    total_records = run_scalar(
        "SELECT COUNT(*) FROM ola_bookings WHERE Booking_Status='Success'"
    )

    st.metric("Total Successful Bookings", f"{total_records:,}")

    page_size = 100
    total_pages = (total_records + page_size - 1) // page_size
    page = st.selectbox("Select Page", range(1, total_pages + 1))

    offset = (page - 1) * page_size

    query = f"""
    SELECT Booking_ID, Customer_ID, Vehicle_Type, Pickup_Location, Drop_Location
    FROM ola_bookings
    WHERE Booking_Status='Success'
    LIMIT {page_size} OFFSET {offset}
    """

    df = run_query(query)

    st.dataframe(df, use_container_width=True)
    st.write(f"Showing {offset+1} to {min(offset+page_size, total_records)}")


elif selected == "Average Ride Distance":
    st.subheader("RETRIEVE THE AVERAGE RIDE DISTANCE FOR EACH VEHICLE TYPE")
    st.text("This section analyzes the average ride distance covered by each vehicle type. "
    "Comparing average trip lengths across vehicle categories helps identify customer preferences,vehicle utilization patterns, and demand trends. These insights can support fleet management, "
    "pricing strategies, and operational planning.")
    query = """ SELECT Vehicle_Type, ROUND(AVG(Ride_Distance),2) AS AVG_DISTANCE
    FROM ola_bookings
    GROUP BY Vehicle_Type
    ORDER BY Vehicle_Type
    """

    df = run_query(query)
    st.dataframe(df, use_container_width=True)

    

elif selected == "Cancelled Rides":
    st.subheader("GET THE TOTAL NUMBER OF CANCELLED RIDES BY CUSTOMERS")
    st.text("This section displays the total number of rides cancelled by customers.These insights can be used to improve customer satisfaction and reduce cancellation frequency.")


    total = run_scalar("""
        SELECT COUNT(*) FROM ola_bookings
        WHERE Booking_Status='Canceled by Customer'
    """)

    st.metric("Cancelled by Customers", f"{total:,}")

elif selected == "Customers With Highest Ride Cancellation":
    st.subheader("LIST THE TOP 5 CUSTOMERS WHO BOOKED THE HIGHEST NUMBER OF RIDES")
    st.text("This analysis identifies the five customers with the highest ride booking frequency.These insights can support targeted marketing campaigns, reward programs, and customer retention strategies.")


    query = """
    SELECT Customer_ID, COUNT(*) AS No_of_Rides
    FROM ola_bookings
    GROUP BY Customer_ID
    ORDER BY No_of_Rides DESC
    LIMIT 5
    """

    st.table(run_query(query))

elif selected == "Rides Cancelled by Drivers":
    st.subheader("GET THE NUMBER OF RIDES CANCELLED BY DRIVERS DUE TO PERSONAL AND CAR-RELATED ISSUES")
    st.text("This analysis calculates the total number of rides cancelled by drivers because of personal reasons or vehicle-related issues.The insights can be used to improve driver support, vehicle maintenance processes, and overall customer satisfaction.")

    total = run_scalar("""
    SELECT COUNT(*)
    FROM ola_bookings
    WHERE Booking_Status='Canceled by Driver'
    AND Canceled_Rides_by_Driver='Personal & Car related issue'
    """)

    st.metric("Driver Cancellations", f"{total:,}")

elif selected == "Driver's Rating":
    st.subheader("FIND THE MAXIMUM AND MINIMUM DRIVER RATINGS FOR PRIME SEDAN BOOKINGS")
    st.text("This analysis retrieves the highest and lowest driver ratings recorded for Prime Sedan bookings. These insights can support performance monitoring, driver training initiatives, and service quality improvements.")

    st.table(run_query("""
    SELECT Vehicle_Type,
           MAX(Driver_Ratings) AS MAXIMUM_RATING,
           MIN(Driver_Ratings) AS MINIMUM_RATING
    FROM ola_bookings
    WHERE Vehicle_Type='Prime Sedan'
    """))

elif selected == "UPI Rides":
    st.subheader("RETRIEVE ALL RIDES WHERE PAYMENT WAS MADE USING UPI")
    st.text("This analysis displays all ride bookings for which the payment method was UPI.These insights can support payment strategy decisions and enhance the overall customer payment experience.")

    # Get total number of rides with UPI Payment Method
    total = run_scalar("""
    SELECT COUNT(*) FROM ola_bookings
    WHERE Payment_Method='UPI'
    """)

    st.metric("UPI Rides", f"{total:,}")

    page_size = 100
    total = run_scalar("SELECT COUNT(*) FROM ola_bookings WHERE Payment_Method='UPI'")
    pages = (total + page_size - 1) // page_size
    page = st.selectbox("Page", range(1, pages + 1))

    offset = (page - 1) * page_size

    df = run_query(f"""
    SELECT Booking_ID, Customer_ID, Vehicle_Type, Pickup_Location,
           Drop_Location, Booking_Value, Ride_Distance
    FROM ola_bookings
    WHERE Payment_Method='UPI'
    LIMIT {page_size} OFFSET {offset}
    """)

    st.dataframe(df, use_container_width=True)

elif selected == "Average Customer Rating":
    st.subheader("FIND THE AVERAGE CUSTOMER RATING PER VEHICLE TYPE")
    st.text("This analysis calculates the average customer rating for each vehicle type. Comparing ratings across vehicle categories helps evaluate customer satisfaction levels, identify high-performing services, and understand customer preferences.")

    
    st.table(run_query("""
    SELECT Vehicle_Type,
           ROUND(AVG(Customer_Rating),2) AS AVG_CUSTOMER_RATING
    FROM ola_bookings
    GROUP BY Vehicle_Type
    ORDER BY Vehicle_Type
    """))

elif selected == "Total booking value":
    st.subheader("CALCULATE THE TOTAL BOOKING VALUE OF RIDES COMPLETED SUCCESSFULLY")
    st.text("This analysis computes the total booking value generated from rides that were completed successfully. Measuring revenue from completed rides helps assess business performance, track earnings, and evaluate operational efficiency.")

    total = run_scalar("""
    SELECT SUM(Booking_Value)
    FROM ola_bookings
    WHERE Booking_Status='Success'
    """)

    st.metric("Total Booking Value", f"{total:,}")


elif selected == "Incomplete Rides":
    st.subheader("LIST ALL INCOMPLETE RIDES ALONG WITH THE REASON")
    st.text("This analysis retrieves all rides that were not completed and displays the corresponding reason for each incomplete booking.These insights can support process improvements, reduce ride cancellations, and enhance overall service reliability.")

    total = run_scalar("""
    SELECT COUNT(*) FROM ola_bookings
    WHERE Incomplete_Rides='Yes'
    """)

    st.metric("Incomplete Rides", f"{total:,}")

    page_size = 100
    pages = (total + page_size - 1) // page_size
    page = st.selectbox("Page", range(1, pages + 1))

    offset = (page - 1) * page_size

    df = run_query(f"""
    SELECT Booking_ID, Incomplete_Rides_Reason
    FROM ola_bookings
    WHERE Incomplete_Rides='Yes'
    LIMIT {page_size} OFFSET {offset}
    """)

    st.dataframe(df, use_container_width=True)



# ======= Close Connection ========
connection.close()
