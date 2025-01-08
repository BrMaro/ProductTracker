import requests
from bs4 import BeautifulSoup
from datetime import datetime
import sqlite3

products = [
    'https://www.jumia.co.ke/generic-60x60-high-power-binoculars-suitable-for-huntingtraveling-250185969.html',
    'https://www.jumia.co.ke/qwen-tws-wireless-earbuds-headset-with-power-bank-black-116853111.html',
]

session = requests.Session()


def setup_database():
    conn = sqlite3.connect('price_history.db')
    cursor = conn.cursor()

    # Product table
    cursor.execute('''CREATE TABLE IF NOT EXISTS Products (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT,
                        url TEXT,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )''')

    # PriceHistory table
    cursor.execute('''CREATE TABLE IF NOT EXISTS PriceHistory (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        product_id INTEGER,
                        price REAL,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (product_id) REFERENCES products (id)
                    )''')

    conn.commit()
    return conn


def track_price(url, conn):
    cursor = conn.cursor()

    response = session.get(url)
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        price_element = soup.find('span', class_=['-b', '-ubpt'])
        product_name = soup.find('h1', class_='-fs20').text.strip() if soup.find('h1',
                                                                                 class_='-fs20') else 'Unknown Product'

        if price_element:
            price_text = price_element.text.strip()
            price = float(price_text.replace('KSh', '').replace(',', '').strip())

            cursor.execute('INSERT OR IGNORE INTO Products (name, url) VALUES (?, ?)', (product_name, url))
            cursor.execute('SELECT id FROM Products WHERE url = ?', (url,))
            product_id = cursor.fetchone()[0]

            # Insert price history
            cursor.execute('INSERT INTO PriceHistory (product_id, price) VALUES (?, ?)', (product_id, price))
            conn.commit()

            print(f"[{current_time}] {product_name}: KSh {price}")
        else:
            print(f"[{current_time}] Price not found for {product_name}")
    else:
        print(f"[{current_time}] Failed to retrieve the page. Status code: {response.status_code}")


def main():
    conn = setup_database()
    # Track all products
    for product_url in products:
        track_price(product_url, conn)

    conn.close()


if __name__ == "__main__":
    main()
