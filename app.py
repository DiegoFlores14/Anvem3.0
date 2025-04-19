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
    "GerardoTAnvem": {"password": "Gerardo444A", "artist": "Gerardo Torres"},
    "AngelRAnvem": {"password": "Angel758A", "artist": "Angel Rodriguez"},
    "ChristianMAnvem": {"password": "Christian467A", "artist": "Christian Morales"},
    "ErickGAnvem": {"password": "Erick178A", "artist": "Erick Gutiérrez"},
    "IsauroMAnvem": {"password": "Isauro999A", "artist": "Isauro Molinos"},
    "JoseOAnvem": {"password": "Jose412A", "artist": "José Olivas"},
    "JoseRomeroAnvem": {"password": "Jose223A", "artist": "José Romero"},
    "JuanLAnvem": {"password": "Juan111A", "artist": "Juan Limon"},
    "JulianMAnvem": {"password": "Julian657A", "artist": "Julián Mercado"},
    "MacarioCAnvem": {"password": "Macario963A", "artist": "Macario Carvajal"},
    "MichelCAnvem": {"password": "Michel582A", "artist": "Michel Cruz"},
    "OscarRAnvem": {"password": "Oscar333A", "artist": "Oscar Regalado"},
    "RodrigoFAnvem": {"password": "Rodrigo741A", "artist": "Rodrigo Flores"},
    "AnvemT": {"password": "Anvem123A", "artist": "ANVEMTUNES"},
    "AnvemL": {"password": "Anvem321A", "artist": "ANVEM LYRICS"},
    "AnvemP": {"password": "Anvem213A", "artist": "ANVEMPUBLISHING"},
    "DanielNAnvem": {"password": "Daniel874A", "artist": "Daniel Nava"},
    "DanielFAnvem": {"password": "Daniel777A", "artist": "Daniel Fuentes"},
    "DenilsonJAnvem": {"password": "Denilson145A", "artist": "Denilson Jaramillo"},
    "FelipeMAnvem": {"password": "Felipe654A", "artist": "Felipe Manzanares"},
    "FernandoRAnvem": {"password": "Fernando888A", "artist": "Fernando Rivas"},
    "FidelVAnvem": {"password": "Fidel547A", "artist": "Fidel Valenzuela"},
    "GaliaOAnvem": {"password": "Galia912A", "artist": "Galia Ortiz"},
    "JadielJAnvem": {"password": "Jadiel487A", "artist": "Jadiel Jaramillo"},
    "JoseCAnvem": {"password": "Castro479A", "artist": "Jose Castro"},
    "MarcoMAnvem": {"password": "Marco845A", "artist": "Marco Mendoza"},
    "MisaelSAnvem": {"password": "Misael845A", "artist": "Misael Sanchez"},
    "PaulinoSAnvem": {"password": "Paulino663A", "artist": "Paulino Salazar"},
    "SergioEAnvem": {"password": "Sergio332A", "artist": "Sergio Espinoza"},
    "VictorGAnvem": {"password": "Victor143A", "artist": "Victor Garcia"},
    "EmilianoMAnvem": {"password": "Emiliano917A", "artist": "Emiliano Morales"},
    "ErickPAnvem": {"password": "Erick555A", "artist": "Erick Paez"},
    "GustavoCAnvem": {"password": "Gustavo872A", "artist": "Gustavo Castillo"},
    "PabloRAnvem": {"password": "Pablo657A", "artist": "Pablo Rodriguez"},
    "MarcoPAnvem": {"password": "Padilla431A", "artist": "Marco Padilla"},
    "EduardoOAnvem": {"password": "Eduardo678A", "artist": "Eduardo Oveso"},
    "OmarAANVEM": {"password": "Omar712A", "artist": "Omar Anaya"},
    "OscarFAnvem": {"password": "Oscar441A", "artist": "Oscar Flores"},
    "PaulinaSAnvem": {"password": "Paulina478A", "artist": "Paulina Servin"},
    "RamonCAnvem": {"password": "Ramon614A", "artist": "Ramon Cuamea"},
    "VictorVAnvem": {"password": "Valdez455A", "artist": "Victor Valdez"},
    "DavidOAnvem": {"password": "Orlando731A", "artist": "David Orlando"},
    "EduardiGAnvem": {"password": "Gurrola558A", "artist": "Eduardo Gurrola"},
    "PedroVAnvem": {"password": "Pedro111A", "artist": "Pedro Villa"},
    "SamanthaBAnvem": {"password": "Samantha663", "artist": "Samantha Barrón"}
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

import pandas as pd
import openpyxl

def convert_excel_to_csv(file_path):
    """Convierte el archivo de Excel a CSV, asegurando que incluimos solo las últimas 3 filas y la columna correcta."""
    try:
        df_statement = pd.read_excel(file_path, sheet_name="Statement", skiprows=8)
        
        # Mostrar las columnas disponibles para identificar correctamente la columna de pagos
        print("Columnas disponibles en Statement:", df_statement.columns)

        # Tomar solo las últimas 3 filas
        last_rows = df_statement.tail(3)
        print("\nÚltimas 3 filas antes de filtrar columna Royalties:\n", last_rows)

        # Filtrar la columna que realmente contiene los pagos
        last_rows = last_rows[["Royalties"]]  # Usa "Royalties" en lugar de "Q"
        print("\nÚltimas 3 filas de la columna Royalties:\n", last_rows)

        csv_path = file_path.replace(".xlsx", ".csv")  # Generar nombre de archivo CSV
        last_rows.to_csv(csv_path, index=False)  # Guardar en CSV
        return csv_path
    except Exception as e:
        print(f"Error al convertir Excel a CSV: {e}")
        return None

def load_net_payment_from_csv(csv_path):
    """Carga el valor desde CSV, asegurando que leemos la columna correcta."""
    try:
        df = pd.read_csv(csv_path)

        # Verificar que la columna Royalties se cargó
        print("\nColumnas disponibles en CSV:", df.columns)

        # Mostrar las últimas 3 filas del CSV para confirmar los datos
        print("\nÚltimas 3 filas de CSV:\n", df.tail(3))

        # Extraer el último valor válido de la columna Royalties
        total_royalties = df["Royalties"].dropna().astype(str).str.replace(',', '').astype(float).iloc[-1]

        print("\nValor extraído de Royalties:", total_royalties)
        return total_royalties
    except Exception as e:
        print(f"Error al leer CSV: {e}")
        return 0.0

def load_excel_data(artist, quarter, year):
    """Carga los datos del artista desde los archivos de Excel y los optimiza."""
    filename = f"{artist}T{quarter}-{year}.xlsx"
    file_path = os.path.join(DATA_FOLDER, filename)
    sheets_data = {}

    if not os.path.exists(file_path):
        sheets_data["By Song"] = "<p style='color:red;'>Archivo no encontrado.</p>"
        sheets_data["By Source"] = "<p style='color:red;'>Archivo no encontrado.</p>"
        sheets_data["total_royalties"] = 0.0
        return sheets_data

    try:
        df_song = pd.read_excel(file_path, sheet_name="By Song", skiprows=8, nrows=11)  # Solo las primeras 10 canciones
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

    # Convertir Excel a CSV y cargar los datos correctamente desde la columna Royalties
    csv_path = convert_excel_to_csv(file_path)
    if csv_path:
        sheets_data["total_royalties"] = load_net_payment_from_csv(csv_path)
    else:
        sheets_data["total_royalties"] = 0.0

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
