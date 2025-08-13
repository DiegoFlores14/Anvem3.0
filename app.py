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
"PablitoOsorio": {"password": "Pablo159A", "artist": "Pablito Osorio"},
"BadlyRouse": {"password": "Badly996", "artist": "Badly Rouse"},
"CarlosRamirez": {"password": "Pyto", "artist": "Carlos Ramirez"},
"Dazoner": {"password": "Dazoner300A", "artist": "Dazoner"},
"FrankLuka": {"password": "Frank444A", "artist": "Frank Luka"},
"Grupo360": {"password": "Grupo360A", "artist": "Grupo 360"},
"Los2dearriba": {"password": "Los2dearriba009A", "artist": "Los 2 de arriba"},
"LosDragonesdeSinaloa": {"password": "Dragones663A", "artist": "Los Dragones de Sinaloa"},
"PanchitoRenteria": {"password": "Panchito350A", "artist": "Panchito Renteria"},
"Villa5": {"password": "Villa888A", "artist": "Villa 5"},
"WilCaro": {"password": "WilCaro100A", "artist": "Wil Caro"},
"MichelCruz": {"password": "Michel582A", "artist": "Michel Cruz"},
}

# Palabras clave para búsqueda de columnas
POSSIBLE_TITLE_KEYWORDS = ["song", "titulo", "title", "nombre", "cancion", "track"]
POSSIBLE_ROYALTIES_KEYWORDS = ["royalt", "ganancia", "amount", "importe", "revenue"]
POSSIBLE_SOURCE_KEYWORDS = ["source", "fuente", "plataforma"]

# Diccionario para rango de meses según trimestre (sin cambios)
QUARTER_RANGES = {
    "1": "01 JAN - 31 JAN",
    "2": "01 FEB - 28 FEB",
    "3": "01 MAR - 31 MAR",
    "4": "01 APR - 30 APR",
    "5": "01 MAY - 31 MAY",
    "6": "01 JUN - 30 JUN",
    "7": "01 JUL - 31 JUL",
    "8": "01 AUG - 31 AUG",
    "9": "01 SEP - 30 SEP",
    "10": "01 OCT - 30 OCT",
    "11": "01 NOV - 30 NOV",
    "12": "01 DEC - 31 DEC"
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
    df[title_col] = df[title_col].str.upper()  # <-- convierte a mayúsculas
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
    total_others = others["Royalties"].sum()
    total_val = df_sorted["Royalties"].sum()

    # Incluir "Others" solo si representa más del 10%
    if total_others / total_val >= 0.1:
        df_final = pd.concat(
            [top5, pd.DataFrame([["Others", total_others]], columns=["Source", "Royalties"])],
            ignore_index=True
        )
    else:
        df_final = top5

    # Reordenar por Royalties para asegurar que el más grande esté primero
    df_final = df_final.sort_values(by="Royalties", ascending=False).reset_index(drop=True)

    legend_labels = [
        f"{src} - {royalty / df_final['Royalties'].sum() * 100:.1f}%"
        for src, royalty in zip(df_final["Source"], df_final["Royalties"])
    ]

    fig, ax = plt.subplots(figsize=(10, 8), facecolor='none')
    wedges, _ = ax.pie(
        df_final["Royalties"],
        startangle=90,  # Ángulo neutral para que el más grande quede arriba
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
                    total = float(str(df.iloc[i, j + 1]).strip())
                except:
                    total = 0.0
    return total, 0

def generate_balance_bar_chart(future_total, investment, balance):
    labels = ["Total Royalties", "Investment", "Balance"]
    values = [future_total, investment if isinstance(investment, (int, float)) else 0, balance if balance else 0]
    colors = ["#4CAF50", "#F44336", "#2196F3"]

    fig, ax = plt.subplots(figsize=(6, 4), facecolor='none')
    bars = ax.bar(labels, values, color=colors)

    # Mostrar valores arriba de las barras
    for bar in bars:
        yval = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2.0, yval + 0.5, f"${yval:.2f}", ha="center", va="bottom")

    ax.set_ylabel("USD")
    ax.set_title("Balance General")
    plt.tight_layout()

    plt.savefig(os.path.join(GENERATED_FOLDER, "balance_bar_chart.png"), transparent=True)
    plt.close()

def extract_net_payment_from_by_song(file_path):
    try:
        df = pd.read_excel(file_path, sheet_name="By Song", skiprows=8, dtype=str)
        df = df.fillna('')  # Evita NaNs

        for i in range(len(df)):
            for j in range(len(df.columns)):
                cell_value = str(df.iloc[i, j]).strip().lower()
                if "net payment" in cell_value:
                    
                    if j + 1 < len(df.columns):
                        value = df.iloc[i, j + 1]
                    
                    elif j > 0:
                        value = df.iloc[i, j - 1]
                    
                    else:
                        value = ""

                    value = str(value).replace(",", "").replace("$", "").strip()
                    try:
                        return round(float(value), 2)
                    except:
                        return 0.0
        return 0.0
    except Exception as e:
        print(f"Error al extraer 'Net Payment' desde 'By Song': {e}")
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

    sheets_data["total_royalties"] = extract_net_payment_from_by_song(file_path)
    
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
                payment = extract_net_payment_from_by_song(file_path)
                total += float(payment or 0)
            except Exception as e:
                print(f"Error leyendo archivo {filename}: {e}")
                continue

    return round(total, 2)

def get_investment_amount(quarter, year):
    investment_file = os.path.join(DATA_FOLDER, "inversion.xlsx")
    
    if not os.path.exists(investment_file):
        return "No se han realizado inversiones"

    try:
        df = pd.read_excel(investment_file)
        df.columns = [str(col).strip().lower() for col in df.columns]

        # Buscar coincidencias por año y trimestre
        match = df[
            (df["año"] == int(year)) &
            (df["trimestre"] == int(quarter))
        ]

        if not match.empty:
            amount = match.iloc[0]["inversión"]
            return round(float(amount), 2)
        else:
            return "No se han realizado inversiones"
    except Exception as e:
        print(f"Error leyendo inversión: {e}")
        return "No se han realizado inversiones"



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

    user_info = USERS.get(session["user"])
    artist = user_info["artist"]
    artist_name = user_info.get("name", artist)  # por si tienes un nombre bonito
    artist_image = f"images/{artist}.jpg"

    # Obtener los archivos disponibles
    all_files = os.listdir(DATA_FOLDER)
    pattern = re.compile(re.escape(artist) + r"T(\d)-(\d{4})\.xlsx")
    matched = [m for m in (pattern.match(f) for f in all_files) if m]

    # Obtener años y trimestres disponibles
    available_years = sorted(set(m.group(2) for m in matched))
    selected_year = request.args.get("year") or (available_years[-1] if available_years else "2024")
    available_quarters = sorted(set(m.group(1) for m in matched if m.group(2) == selected_year), reverse=True)
    selected_quarter = request.args.get("quarter") or (available_quarters[0] if available_quarters else "1")

    return render_template(
        "dashboard.html",
        artist_name=artist_name,
        artist_image=artist_image,
        selected_year=selected_year,
        selected_quarter=selected_quarter,
        available_years=available_years,
        available_quarters=available_quarters
    )


@app.route("/load_dashboard_data")
def load_dashboard_data():
    if "user" not in session:
        return {"error": "Unauthorized"}, 401

    artist = USERS[session["user"]]["artist"]
    selected_year = request.args.get("year")
    selected_quarter = request.args.get("quarter")

    sheets_data = load_excel_data(artist, selected_quarter, selected_year)
    future_total = calculate_future_total(artist, selected_quarter, selected_year)
    investment = get_investment_amount(selected_quarter, selected_year)

    # Verifica si la inversión es numérica antes de calcular el balance
    if isinstance(investment, (int, float)):
        balance = round(future_total - investment, 2)
    else:
        balance = None

    generate_balance_bar_chart(future_total, investment, balance)
    quarter_key = selected_quarter.replace("T", "")
    quarter_range = QUARTER_RANGES.get(quarter_key, "Desconocido")

    return {
        "sheets": {
            "by_song": sheets_data["By Song"],
            "by_source": sheets_data["By Source"],
            "total_royalties": sheets_data["total_royalties"]
        },
        "future_total": future_total,
        "investment": investment,
        "balance": balance,
        "quarter_dates": f"{quarter_range} {selected_year}"
    }


@app.route("/download_statement")
def download_statement():
    if "user" not in session:
        return redirect(url_for("login"))
    artist = USERS[session["user"]]["artist"]
    quarter = request.args.get("quarter")
    year = request.args.get("year")
    filename = f"{artist}A{quarter}-{year}.xlsx"
    file_path = os.path.join(DATA_FOLDER, filename)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    return "Archivo no encontrado", 404

if __name__ == "__main__":
    app.run(debug=True)
