import os
import re
import pandas as pd
import matplotlib.pyplot as plt
from flask import Flask, render_template, request, session, redirect, url_for, send_file

app = Flask(__name__)
app.secret_key = "clave_secreta"  # Ajusta tu clave segura según lo necesites
DATA_FOLDER = os.path.join(app.root_path, "data")
GENERATED_FOLDER = os.path.join(app.root_path, "static", "generated")
os.makedirs(GENERATED_FOLDER, exist_ok=True)

# Usuarios y sus artistas (conserva la estructura original)
USERS = {
    "gerardo": {"password": "gerardo123", "artist": "Gerardo Torres"},
    "angel": {"password": "angel123", "artist": "Angel Rogriguez"},
    "christian": {"password": "christian123", "artist": "Christian Morales"},
    "erick": {"password": "erick123", "artist": "Erick Gutiérrez"},
    "isauro": {"password": "isauro123", "artist": "Isauro Molinos"},
    "olivas": {"password": "olivas123", "artist": "José Olivas"},
    "romero": {"password": "romero123", "artist": "José Romero"},
    "limon": {"password": "limon123", "artist": "Juan Limon"},
    "julian": {"password": "julian123", "artist": "Julián Mercado"},
    "macario": {"password": "macario123", "artist": "Macario Carvajal"},
    "michel": {"password": "michel123", "artist": "Michel Cruz"},
    "oscar": {"password": "oscar123", "artist": "Oscar Regalado"},
    "rodrigo": {"password": "rodrigo123", "artist": "Rodrigo Flores"},
    "anvemT": {"password": "anvem123", "artist": "ANVEMTUNES"},
    "anvemL": {"password": "anvem123", "artist": "ANVEM LYRICS"},
    "anvemP": {"password": "anvem123", "artist": "ANVEMPUBLISHING"},
    "daniel": {"password": "daniel123", "artist": "Daniel Nava"},
    "fuentes": {"password": "fuentes123", "artist": "Daniel Fuentes"},
    "denilson": {"password": "denilson123", "artist": "Denilson Jaramillo"},
    "felipe": {"password": "felipe123", "artist": "Felipe Manzanares"},
    "fernando": {"password": "fernando123", "artist": "Fernando Rivas"},
    "fidel": {"password": "fidel123", "artist": "Fidel Valenzuela"},
    "galia": {"password": "galia123", "artist": "Galia Ortiz"},
    "jadiel": {"password": "jadiel123", "artist": "Jadiel Jaramillo"},
    "castro": {"password": "castro123", "artist": "Jose Castro"},
    "marco": {"password": "marco123", "artist": "Marco Mendoza"},
    "misael": {"password": "misael123", "artist": "Misael Sanchez"},
    "paulino": {"password": "paulino123", "artist": "Paulino Salazar"},
    "sergio": {"password": "sergio123", "artist": "Sergio Espinoza"},
    "victor": {"password": "victor123", "artist": "Victor Garcia"},
    "emiliano": {"password": "emiliano123", "artist": "Emiliano Morales"},
    "paez": {"password": "paez123", "artist": "Erick Paez"},
    "gustavo": {"password": "gustavo123", "artist": "Gustavo Castillo"},
    "pablo": {"password": "pablo123", "artist": "Pablo Rodriguez"},
    "padilla": {"password": "padilla123", "artist": "Marco Padilla"},
    "eduardo": {"password": "eduardo123", "artist": "Eduardo Oveso"},
    "omar": {"password": "omar123", "artist": "Omar Anaya"},
    "flores": {"password": "flores123", "artist": "Oscar Flores"},
    "paulina": {"password": "paulina123", "artist": "Paulina Servin"},
    "ramon": {"password": "ramon123", "artist": "Ramon Cuamea"},
    "valdez": {"password": "valdez123", "artist": "Victor Valdez"},
    "orlando": {"password": "orlando123", "artist": "David Orlando"},
    "gurrola": {"password": "gurrola123", "artist": "Eduardo Gurrola"},
    "pedro": {"password": "pedro123", "artist": "Pedro Villa"},
    "samantha": {"password": "samantha123", "artist": "Samantha Barrón"}
}

# Palabras clave para búsqueda de columnas
POSSIBLE_TITLE_KEYWORDS = ["song", "titulo", "title", "nombre", "cancion", "track"]
POSSIBLE_ROYALTIES_KEYWORDS = ["royalt", "ganancia", "amount", "importe", "revenue"]
POSSIBLE_SOURCE_KEYWORDS = ["source", "fuente", "plataforma"]

# Diccionario para rango de meses según trimestre (sin cambios)
QUARTER_RANGES = {
    "1": "01 JAN - 31 MAR",
    "2": "01 APR - 30 JUN",
    "3": "01 JUL - 30 SEP",
    "4": "01 OCT - 31 DEC"
}

def find_column(df, keywords, fallback_to_first=True):
    for col in df.columns:
        if any(kw in col.lower() for kw in keywords):
            return col
    return df.columns[0] if fallback_to_first else None

def clean_by_song(df):
    df.drop(columns=[c for c in df.columns if "unit" in c.lower()], inplace=True, errors="ignore")
    title_col = find_column(df, POSSIBLE_TITLE_KEYWORDS)
    royalties_col = find_column(df, POSSIBLE_ROYALTIES_KEYWORDS)
    df = df[[title_col, royalties_col]].copy()
    df.columns = ["Song", "Royalties"]
    df.dropna(subset=["Song"], inplace=True)
    df = df[~df["Song"].str.contains("TOTAL", case=False, na=False)]
    df["Royalties"] = pd.to_numeric(df["Royalties"], errors="coerce").fillna(0)
    return df.nlargest(10, "Royalties")

def clean_by_source(df):
    df.drop(columns=[c for c in df.columns if "unit" in c.lower()], inplace=True, errors="ignore")
    source_col = find_column(df, POSSIBLE_SOURCE_KEYWORDS)
    royalties_col = find_column(df, POSSIBLE_ROYALTIES_KEYWORDS)
    df = df[[source_col, royalties_col]].copy()
    df.columns = ["Source", "Royalties"]
    df.dropna(subset=["Source"], inplace=True)
    df = df[~df["Source"].str.contains("TOTAL", case=False, na=False)]
    df["Royalties"] = pd.to_numeric(df["Royalties"], errors="coerce").fillna(0)
    return df

def generate_source_pie_chart(df):
    df_sorted = df.sort_values(by="Royalties", ascending=False)
    top5 = df_sorted.head(5)
    others = df_sorted.iloc[5:]
    if not others.empty:
        total_others = others["Royalties"].sum()
        df_final = pd.concat([top5, pd.DataFrame([["Others", total_others]], columns=["Source", "Royalties"])], ignore_index=True)
    else:
        df_final = top5

    total_val = df_final["Royalties"].sum()
    legend_labels = [
        f"{src} - {royalty/total_val*100:.1f}%"
        for src, royalty in zip(df_final["Source"], df_final["Royalties"])
    ]

    fig, ax = plt.subplots(figsize=(10, 8), facecolor='none')
    wedges, _ = ax.pie(
        df_final["Royalties"],
        startangle=140,
        labels=None,
        wedgeprops=dict(edgecolor='white')
    )
    ax.axis('equal')
    plt.legend(
        wedges,
        legend_labels,
        title="Plataformas",
        loc="center left",
        bbox_to_anchor=(1, 0.5),
        labelspacing=1.3,
        prop={'size': 14},
        frameon=False
    )
    plt.tight_layout()
    plt.savefig(os.path.join(GENERATED_FOLDER, "source_pie_chart.png"), transparent=True)
    plt.close()

def generate_song_bar_chart(df):
    df_sorted = df.sort_values(by="Royalties", ascending=False).head(10)
    fig, ax = plt.subplots(figsize=(10, 6), facecolor='none')
    ax.bar(df_sorted["Song"], df_sorted["Royalties"], color="steelblue")
    ax.set_ylabel("Royalties")
    ax.set_title("Top 10 Songs")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig(os.path.join(GENERATED_FOLDER, "song_bar_chart.png"), transparent=True)
    plt.close()

def clean_statement(df, quarter):
    df.columns = [str(col).strip() for col in df.columns]
    total = 0.0
    for i in range(df.shape[0]):
        for j in range(df.shape[1] - 1):
            if re.search(r"total\s*royalties", str(df.iloc[i, j]).lower()):
                try:
                    total = float(str(df.iloc[i, j+1]).strip())
                except:
                    total = 0.0
    return total, 0

import openpyxl

def load_excel_data(artist, quarter, year):
    filename = f"{artist}T{quarter}-{year}.xlsx"
    file_path = os.path.join(DATA_FOLDER, filename)
    sheets_data = {}

    if not os.path.exists(file_path):
        sheets_data["By Song"] = "<p style='color:red;'>Archivo no encontrado.</p>"
        sheets_data["By Source"] = "<p style='color:red;'>Archivo no encontrado.</p>"
        sheets_data["total_royalties"] = 0.0
        return sheets_data

    try:
        df_song = pd.read_excel(file_path, sheet_name="By Song", skiprows=8, nrows=11)
        df_song_clean = clean_by_song(df_song)
        generate_song_bar_chart(df_song_clean)
        sheets_data["By Song"] = df_song_clean.to_html(
            header=False,
            index=False,
            border=0,
            float_format="%.2f",
            classes="table table-transparent text-center align-middle",
            formatters={
                "Song": lambda x: f'<td style="text-align: left;">{x}</td>',
                "Royalties": lambda x: f'<td style="text-align: right;">{x:.2f}</td>'
            },
            escape=False
        )
    except Exception as e:
        sheets_data["By Song"] = f"<p style='color:red;'>Error 'By Song': {e}</p>"

    try:
        df_source = pd.read_excel(file_path, sheet_name="By Source", skiprows=8)
        df_source_clean = clean_by_source(df_source)
        generate_source_pie_chart(df_source_clean)
        top3 = df_source_clean.nlargest(5, "Royalties")
        sheets_data["By Source"] = top3.to_html(
            header=False,
            index=False,
            border=0,
            float_format="%.2f",
            classes="table table-transparent text-center align-middle",
            formatters={
                "Source": lambda x: f'<td style="text-align: left;">{x}</td>',
                "Royalties": lambda x: f'<td style="text-align: right;">{x:.2f}</td>'
            },
            escape=False
        )
    except Exception as e:
        sheets_data["By Source"] = f"<p style='color:red;'>Error 'By Source': {e}</p>"

    try:
        # Cargar el archivo con openpyxl para mejorar el rendimiento
        wb = openpyxl.load_workbook(file_path, data_only=True)
        sheet = wb["Statement"]

        total_royalties = 0.0  # Inicializar variable
        for row in sheet.iter_rows(min_row=sheet.max_row - 3, max_row=sheet.max_row):  # Solo escanea las últimas 3 filas
            net_payment_cell = row[15]  # Columna P (índice 15 en openpyxl)
            amount_cell = row[16]  # Columna Q (índice 16 en openpyxl)
            
            if net_payment_cell.value and isinstance(net_payment_cell.value, str) and "Net Payment" in net_payment_cell.value:
                try:
                    total_royalties = float(amount_cell.value or 0)  # Captura el valor de la celda en columna Q
                except ValueError:
                    total_royalties = 0.0
                break
        
        sheets_data["total_royalties"] = total_royalties
    except Exception as e:
        sheets_data["total_royalties"] = 0.0
        print(f"Error en carga de royalties: {e}")  # Imprime el error en caso de falla

    return sheets_data


def calculate_future_total(artist, selected_quarter, selected_year):
    all_files = os.listdir(DATA_FOLDER)
    pattern = re.compile(re.escape(artist) + r"T(\d)-(\d{4})\.xlsx")
    matched = [m for m in (pattern.match(f) for f in all_files) if m]
    total = 0.0
    for m in matched:
        q = int(m.group(1))
        y = int(m.group(2))
        if y == int(selected_year) and q <= int(selected_quarter):
            filename = f"{artist}T{q}-{selected_year}.xlsx"
            file_path = os.path.join(DATA_FOLDER, filename)
            try:
                df = pd.read_excel(file_path, sheet_name="Statement", skiprows=8)
                tr, _ = clean_statement(df, m.group(1))
                total += float(tr or 0)
            except:
                continue
    return total * 0.9

@app.route("/")
def index():
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if username in USERS and USERS[username]["password"] == password:
            session["user"] = username
            return redirect(url_for("dashboard"))
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))

@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("login"))
    
    artist = USERS[session["user"]]["artist"]
    all_files = os.listdir(DATA_FOLDER)
    pattern = re.compile(re.escape(artist) + r"T(\d)-(\d{4})\.xlsx")
    matched = [m for m in (pattern.match(f) for f in all_files) if m]
    available_years = sorted(set(m.group(2) for m in matched))
    selected_year = request.args.get("year") or (available_years[-1] if available_years else "2024")
    available_quarters = sorted(set(m.group(1) for m in matched if m.group(2) == selected_year), reverse=True)
    selected_quarter = request.args.get("quarter") or (available_quarters[0] if available_quarters else "1")
    
    sheets_data = load_excel_data(artist, selected_quarter, selected_year)
    future_total = calculate_future_total(artist, selected_quarter, selected_year)
    
    # Se usa el valor sin "T" para obtener el rango
    quarter_key = selected_quarter.replace("T", "")
    quarter_range = QUARTER_RANGES.get(quarter_key, "Desconocido")
    
    artist_image = f"images/{artist}.jpg"
    
    return render_template("dashboard.html",
        sheets=sheets_data,
        selected_quarter=selected_quarter,
        available_quarters=[f"{q}" for q in available_quarters],
        selected_year=selected_year,
        available_years=available_years,
        # En el contenedor de FUTURE se mostrará "Total Earned {selected_year}"
        quarter_label=f"Total Earned {selected_year}",
        quarter_dates=f"{quarter_range} {selected_year}",
        artist_name=artist,
        artist_image=artist_image,
        future_total=future_total
    )

@app.route("/download_statement")
def download_statement():
    if "user" not in session:
        return redirect(url_for("login"))
    artist = USERS[session["user"]]["artist"]
    quarter = request.args.get("quarter")
    year = request.args.get("year")
    filename = f"{artist}T{quarter}-{year}.xlsx"
    file_path = os.path.join(DATA_FOLDER, filename)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    return "Archivo no encontrado", 404

if __name__ == "__main__":
    app.run(debug=True)
