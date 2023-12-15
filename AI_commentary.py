from openai import OpenAI
import sqlite3
from pprint import pprint
import time

api_key = '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'

client = OpenAI(
  api_key=api_key,  # this is also the default, it can be omitted
)

def generate_commentary(prompt):
    try:
        response = client.chat.completions.create(
            model="ft:gpt-3.5-turbo-1106:tradetech::8VrV3gZK",
            messages=[
                {"role": "system", "content": "Hebrew Syntax, Morphology and Etymology Analysis."},
                {"role": "user", "content": prompt}
            ]
        )
        analysis = response.choices[0].message.content
        return analysis
    except Exception as e:
        print(f"Error generating commentary: {e}")
        raise  # Stop the script if an error occurs

# Connect to SQLite3 database
conn = sqlite3.connect('rbt_hebrew_commentary.sqlite3')
cursor = conn.cursor()

# Create a table to store commentary if it doesn't exist
cursor.execute('''
    CREATE TABLE IF NOT EXISTS hebrew_analysis (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        reference TEXT,
        commentary TEXT
    )
''')
conn.commit()

progress_file = 'progress.txt'

def save_progress(line_number):
    with open(progress_file, 'w') as progress:
        progress.write(str(line_number))

def get_progress():
    try:
        with open(progress_file, 'r') as progress:
            return int(progress.read())
    except FileNotFoundError:
        return 0

# Start from the last saved progress
start_line = get_progress()

with open('output.txt', 'r', encoding='utf-8') as file:
    for line_number, line in enumerate(file, start=start_line):
        # Assuming the reference is separated by space or tab
        parts = line.strip().split(None, 1)

        if len(parts) == 2:
            reference, hebrew_text = parts

            book = 'Genesis '
            reference = book + reference

            prompt = "Analyze every word: " + hebrew_text
            print(f"Line {line_number + 1} - {reference}")
            print(prompt)

            try:
                commentary = generate_commentary(prompt)
                pprint(commentary)

                # Insert the result into the SQLite3 table
                cursor.execute('''
                    INSERT INTO hebrew_analysis (reference, commentary)
                    VALUES (?, ?)
                ''', (reference, commentary))
                conn.commit()

                # Save progress after each successful line
                save_progress(line_number + 1)

            except KeyboardInterrupt:
                print("Script interrupted by user.")
                break

            except Exception as e:
                print(f"Error processing line {line_number + 1}: {e}")

        # Add a sleep to avoid reaching API rate limits
        time.sleep(2)

# Close the connection after processing
conn.close()