from dash import Dash, html, dcc, Input, Output, State, no_update
import dash_bootstrap_components as dbc
import pandas as pd
from conexion_bd import (
    crear_usuario,
    verificar_credenciales,
    asignar_ubicacion,
    liberar_ubicacion,
    obtener_opciones_disponibles,
    obtener_todas_las_posiciones,
)

# --- Inicialización de la Aplicación ---
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], suppress_callback_exceptions=True)

# --- Layouts ---
def sidebar():
    """Barra lateral con enlaces de navegación."""
    return dbc.Col(
        dbc.Nav(
            [
                dbc.NavLink("Gestión", href="/gestion", active="exact"),
                dbc.NavLink("Liberar Ubicación", href="/liberar", active="exact"),
                dbc.NavLink("Visualización", href="/visualizacion", active="exact"),
                dbc.NavLink("Cerrar Sesión", href="/", active="exact"),
            ],
            vertical=True,
            pills=True,
        ),
        width=2,
        style={
            "backgroundColor": "#f8f9fa",
            "padding": "20px",
            "height": "100vh",
        },
    )



def login_layout():
    """Layout para la página de inicio de sesión."""
    return html.Div(
        style={
            "backgroundImage": 'url("/assets/almacen.jpg")',
            "backgroundSize": "cover",
            "height": "100vh",
            "display": "flex",
            "flexDirection": "column",
            "justifyContent": "center",
            "alignItems": "center",
        },
        children=[
            html.Div(id="login-content", children=[  # Cambiado el id a "login-content"
                html.H1(
                    "Bienvenidos al sistema de control de inventario",
                    style={
                        "color": "black",
                        "textAlign": "center",
                        "marginBottom": "30px",
                        "fontSize": "2.5rem",
                        "textShadow": "2px 2px 5px rgba(0, 0, 0, 0.5)",
                    },
                ),
                dbc.Card(
                    dbc.CardBody([
                        html.H4("Iniciar Sesión", className="card-title", style={"textAlign": "center"}),
                        dbc.Input(id="login-username", placeholder="Usuario", type="text", className="mb-2"),
                        dbc.Input(id="login-password", placeholder="Contraseña", type="password", className="mb-3"),
                        dbc.Button("Ingresar", id="login-button", color="primary", className="w-100"),
                        html.Div(id="login-feedback", className="mt-2 text-danger"),
                        dbc.Button(
                            "Crear nuevo usuario",
                            id="open-create-user-modal",
                            color="secondary",
                            className="mt-3 w-100",
                        ),
                    ]),
                    style={
                        "width": "400px",
                        "padding": "20px",
                        "boxShadow": "0px 4px 10px rgba(0, 0, 0, 0.3)",
                        "margin": "auto",
                        "displey": "block"
                    },
                ),
                # Modal para crear usuario
                dbc.Modal(
                    [
                        dbc.ModalHeader(dbc.ModalTitle("Crear Usuario")),
                        dbc.ModalBody([
                            dbc.Input(id="new-username", placeholder="Nuevo Usuario", type="text", className="mb-2"),
                            dbc.Input(id="new-password", placeholder="Nueva Contraseña", type="password", className="mb-3"),
                            html.Div(id="create-user-feedback", className="mt-2 text-danger"),  # Feedback agregado aquí
                        ]),
                        dbc.ModalFooter([
                            dbc.Button("Crear Usuario", id="create-user-button", color="primary"),
                            dbc.Button("Cerrar", id="close-create-user-modal", className="ms-2"),
                        ]),
                    ],
                    id="create-user-modal",
                    is_open=False,
                ),
            ]),
        ],
    )


def gestion_layout():
    """Layout para la página de gestión de ubicaciones."""
    return html.Div([
        dbc.Row([
            sidebar(),
            dbc.Col(
                dbc.Container([
                    html.H2("Gestión de Ubicaciones de Pallets"),
                    dbc.Row([
                        dbc.Col([
                            dcc.Dropdown(id="tipo-almacen-select", placeholder="Seleccione Tipo de Almacén", options=[]),
                            dcc.Dropdown(id="piso-select", placeholder="Seleccione Piso", options=[]),
                            dcc.Dropdown(id="rack-select", placeholder="Seleccione Rack", options=[]),
                            dcc.Dropdown(id="letra-select", placeholder="Seleccione Letra", options=[]),
                            dbc.Input(id="pallet-id", placeholder="ID del Pallet", type="text", className="mt-2"),
                            dbc.Button("Asignar Ubicación", id="assign-button", className="mt-3", color="success"),
                            html.Div(id="assign-feedback", className="mt-3"),
                        ], width=6),
                    ]),
                ]),
                width=10,
            ),
        ]),
    ])

def liberar_layout():
    """Layout para la página de liberación de ubicaciones."""
    return html.Div([
        dbc.Row([
            sidebar(),
            dbc.Col(
                dbc.Container([
                    html.H2("Liberar Ubicación de Pallet"),
                    dbc.Row([
                        dbc.Col([
                            dbc.Input(id="pallet-id-liberar", placeholder="ID del Pallet para liberar", type="text", className="mb-2"),
                            dbc.Button("Liberar Ubicación", id="liberar-button", color="danger", className="mt-3"),
                            html.Div(id="liberar-feedback", className="mt-3"),
                        ], width=6),
                    ]),
                ]),
                width=10,
            ),
        ]),
    ])


def visualizacion_layout():
    """Layout para la página de visualización del almacén."""
    posiciones = obtener_todas_las_posiciones()

    try:
        df_posiciones = pd.DataFrame.from_records(posiciones, columns=[
            "Tipo Almacén", "Piso", "Rack", "Letra", "Posición Pallet", "Estado Ubicación", 
            "id_pallet_asignado", "Descripción", "Fecha Ingreso"
        ])
    except ValueError as e:
        return html.Div([dbc.Alert(f"Error al crear DataFrame: {e}", color="danger")])

    # Reemplaza valores nulos con "Libre"
    df_posiciones["id_pallet_asignado"] = df_posiciones["id_pallet_asignado"].fillna("Libre")

    # Dropdowns para filtrar
    filtro_dropdown = dcc.Dropdown(
        id="filtro-id-pallet",
        options=[
            {"label": val, "value": val} for val in df_posiciones["id_pallet_asignado"].unique() if val != "Libre"
        ],
        placeholder="Seleccione uno o más ID de Pallet",
        multi=True,
        style={"marginBottom": "20px"}
    )
    filtro_descripcion_dropdown = dcc.Dropdown(
        id="filtro-descripcion-pallet",
        options=[
            {"label": val, "value": val} for val in df_posiciones["Descripción"].dropna().unique()
        ],
        placeholder="Seleccione una o más Descripciones",
        multi=True,
        style={"marginBottom": "20px"}
    )
    filtro_fecha_dropdown = dcc.Dropdown(
        id="filtro-fecha-ingreso",
        options=[
            {"label": str(val), "value": str(val)} for val in df_posiciones["Fecha Ingreso"].dropna().unique()
        ],
        placeholder="Seleccione una o más Fechas",
        multi=True,
        style={"marginBottom": "20px"}
    )

    # Columna derecha con métricas generales, filtros y otras estadísticas
    columna_derecha = html.Div([
        # Métricas generales
        html.H4("Resumen General", className="text-primary", style={"marginBottom": "20px"}),

        # Utilización general
        html.Div([
            html.H5("Utilización General:", style={"marginBottom": "5px"}),
            html.H2(id="utilizacion-general-html", className="text-success"),  # ID para callback
        ], style={"marginBottom": "20px"}),

        # Espacios disponibles generales
        html.Div([
            html.H5("Espacios Disponibles Totales:", style={"marginBottom": "5px"}),
            html.H2(id="espacios-disponibles-general-html", className="text-success"),  # ID para callback
        ]),
        html.Hr(),

        # Filtros
        html.H5("Filtrar por ID de Pallet", style={"marginTop": "20px"}),
        filtro_dropdown,
        html.H5("Filtrar por Descripción", style={"marginTop": "20px"}),
        filtro_descripcion_dropdown,
        html.H5("Filtrar por Fecha de Ingreso", style={"marginTop": "20px"}),
        filtro_fecha_dropdown,
        html.Hr(),
    ], style={
        "backgroundColor": "#f8f9fa",
        "padding": "20px",
        "borderRadius": "5px",
    })

    # Layout completo
    return html.Div([
        dbc.Row([
            # Barra lateral
            dbc.Col(
                sidebar(),
                xs=12, sm=12, md=3, lg=2, xl=2,  # Barra lateral ocupa 2 columnas en pantallas grandes
                style={"backgroundColor": "#f8f9fa", "padding": "20px", "minHeight": "100vh"}
            ),
            # Contenido principal
            dbc.Col(
                dbc.Container([
                    html.H2("Visualización del Almacén", style={"marginBottom": "30px"}),

                    # Rack 1
                    html.Div([
                        html.Div([
                            html.Div([
                                html.H4("Utilización:", className="text-primary", style={"marginRight": "10px", "display": "inline-block"}),
                                html.H2(id="utilizacion-rack1-html", className="text-success", style={"marginRight": "30px", "display": "inline-block"}),  # ID para callback
                                html.H4("Espacios disponibles:", className="text-primary", style={"marginRight": "10px", "display": "inline-block"}),
                                html.H2(id="disponibles-rack1-html", className="text-success", style={"display": "inline-block"}),  # ID para callback
                            ], style={"display": "flex", "alignItems": "center", "marginBottom": "15px"}),  # Flexbox para alineación horizontal
                        ]),
                        html.Div(id="rack1-html"),  # Tabla de Rack 1
                    ], style={"marginBottom": "50px"}),

                    # Rack 2
                    html.Div([
                        html.Div([
                            html.Div([
                                html.H4("Utilización:", className="text-primary", style={"marginRight": "10px", "display": "inline-block"}),
                                html.H2(id="utilizacion-rack2-html", className="text-success", style={"marginRight": "30px", "display": "inline-block"}),  # ID para callback
                                html.H4("Espacios disponibles:", className="text-primary", style={"marginRight": "10px", "display": "inline-block"}),
                                html.H2(id="disponibles-rack2-html", className="text-success", style={"display": "inline-block"}),  # ID para callback
                            ], style={"display": "flex", "alignItems": "center", "marginBottom": "15px"}),  # Flexbox para alineación horizontal
                        ]),
                        html.Div(id="rack2-html"),  # Tabla de Rack 2
                    ]),
                ]),
                xs=12, sm=12, md=7, lg=8, xl=8,  # Ajusta el tamaño del contenido principal
            ),
            # Columna derecha con métricas generales y filtros
            dbc.Col(
                columna_derecha,
                xs=12, sm=12, md=3, lg=2, xl=2,  # Columna derecha ocupa 2 columnas en pantallas grandes
            ),
        ], className="g-0"),
    ])



@app.callback(
    [Output("rack1-html", "children"),
     Output("rack2-html", "children"),
     Output("utilizacion-rack1-html", "children"),
     Output("utilizacion-rack2-html", "children"),
     Output("disponibles-rack1-html", "children"),
     Output("disponibles-rack2-html", "children"),
     Output("utilizacion-general-html", "children"),  # Nueva salida
     Output("espacios-disponibles-general-html", "children")],  # Nueva salida
    [Input("filtro-id-pallet", "value"),
     Input("filtro-descripcion-pallet", "value"),
     Input("filtro-fecha-ingreso", "value")]
)
def actualizar_colores(filtro_ids, filtro_descripcion, filtro_fechas):
    """Actualiza las tablas, la utilización, los espacios disponibles y las métricas generales."""
    posiciones = obtener_todas_las_posiciones()
    df_posiciones = pd.DataFrame.from_records(posiciones, columns=[
        "Tipo Almacén", "Piso", "Rack", "Letra", "Posición Pallet", "Estado Ubicación",
        "id_pallet_asignado", "Descripción", "Fecha Ingreso"
    ])
    df_posiciones["id_pallet_asignado"] = df_posiciones["id_pallet_asignado"].fillna("Libre")

    # Filtrar datos por racks
    df_rack1 = df_posiciones[df_posiciones["Rack"] == 1]
    df_rack2 = df_posiciones[df_posiciones["Rack"] == 2]

    # Calcular utilización y espacios disponibles por rack
    total_rack1 = len(df_rack1)
    total_rack2 = len(df_rack2)
    ocupados_rack1 = len(df_rack1[df_rack1["id_pallet_asignado"] != "Libre"])
    ocupados_rack2 = len(df_rack2[df_rack2["id_pallet_asignado"] != "Libre"])
    disponibles_rack1 = total_rack1 - ocupados_rack1
    disponibles_rack2 = total_rack2 - ocupados_rack2
    utilizacion_rack1 = f"{(ocupados_rack1 / total_rack1 * 100):.2f}%" if total_rack1 > 0 else "0.00%"
    utilizacion_rack2 = f"{(ocupados_rack2 / total_rack2 * 100):.2f}%" if total_rack2 > 0 else "0.00%"

    # Calcular métricas generales
    total_general = total_rack1 + total_rack2
    ocupados_general = ocupados_rack1 + ocupados_rack2
    disponibles_general = total_general - ocupados_general
    utilizacion_general = f"{(ocupados_general / total_general * 100):.2f}%" if total_general > 0 else "0.00%"

    # Crear matrices dinámicas
    matriz_rack1 = pd.crosstab(
        index=[df_rack1["Piso"], df_rack1["Posición Pallet"]],
        columns=df_rack1["Letra"],
        values=df_rack1["id_pallet_asignado"],
        aggfunc="first"
    ).fillna("Libre").sort_index(ascending=[False, False])

    matriz_rack2 = pd.crosstab(
        index=[df_rack2["Piso"], df_rack2["Posición Pallet"]],
        columns=df_rack2["Letra"],
        values=df_rack2["id_pallet_asignado"],
        aggfunc="first"
    ).fillna("Libre").sort_index(ascending=[False, False])

    # Función para generar HTML con lógica de color
    def generar_html_matriz(df, titulo, id_filtro, descripcion_filtro, fecha_filtro):
        """Genera una tabla HTML con colores dinámicos basados en los filtros."""
        filas = []
        encabezados = ["Piso", "Posición Pallet"] + list(df.columns)
        filas.append(html.Tr([html.Th(col, style={"textAlign": "center"}) for col in encabezados]))

        for index, row in df.iterrows():
            celdas = []
            piso, posicion = index
            celdas.append(html.Td(piso, style={"textAlign": "center"}))
            celdas.append(html.Td(posicion, style={"textAlign": "center"}))

            for col, val in row.items():
                estilo = {"textAlign": "center", "fontWeight": "bold", "color": "white"}

                if val == "Libre":
                    estilo["backgroundColor"] = "green"
                else:
                    descripcion = df_posiciones.loc[df_posiciones["id_pallet_asignado"] == val, "Descripción"].values[0]
                    fecha = df_posiciones.loc[df_posiciones["id_pallet_asignado"] == val, "Fecha Ingreso"].values[0]

                    if (
                        (filtro_ids and val in filtro_ids) or
                        (filtro_descripcion and descripcion in filtro_descripcion) or
                        (filtro_fechas and str(fecha) in filtro_fechas)
                    ):
                        estilo["backgroundColor"] = "blue"
                    else:
                        estilo["backgroundColor"] = "red"

                celdas.append(html.Td(val, style=estilo))
            filas.append(html.Tr(celdas))

        return html.Div([
            html.H4(titulo, style={"marginTop": "20px", "marginBottom": "10px"}),
            html.Table(filas, className="table table-bordered table-hover", style={"marginTop": "20px"})
        ])

    rack1_html = generar_html_matriz(matriz_rack1, "Rack 1", filtro_ids, filtro_descripcion, filtro_fechas)
    rack2_html = generar_html_matriz(matriz_rack2, "Rack 2", filtro_ids, filtro_descripcion, filtro_fechas)

    return (
        rack1_html,
        rack2_html,
        utilizacion_rack1,
        utilizacion_rack2,
        f"{disponibles_rack1} espacios",
        f"{disponibles_rack2} espacios",
        utilizacion_general,  # Métrica general
        f"{disponibles_general} espacios"  # Métrica general
    )







# --- Callbacks ---
@app.callback(
    Output("page-content", "children"),
    Input("url", "pathname")  # Cambia el contenido según la ruta
)
def display_page(pathname):
    if pathname == "/gestion":
        return gestion_layout()  # Página de gestión
    elif pathname == "/liberar":
        return liberar_layout()  # Página de liberar ubicación
    elif pathname == "/visualizacion":
        return visualizacion_layout()  # Página de visualización
    return login_layout()  # Página de inicio de sesión


@app.callback(
    [
        Output("assign-feedback", "children"),
        Output("tipo-almacen-select", "options"),
        Output("piso-select", "options"),
        Output("rack-select", "options"),
        Output("letra-select", "options"),
    ],
    [
        Input("assign-button", "n_clicks"),
        State("tipo-almacen-select", "value"),
        State("piso-select", "value"),
        State("rack-select", "value"),
        State("letra-select", "value"),
        State("pallet-id", "value"),
    ],
)
def asignar_y_refrescar(n_clicks, tipo_almacen, piso, rack, letra, pallet_id):
    # Obtener las opciones disponibles
    tipos_almacen, pisos, racks, letras = obtener_opciones_disponibles(
        tipo_almacen=tipo_almacen, piso=piso, rack=rack, letra=letra
    )
    tipos_almacen_options = [{"label": t, "value": t} for t in tipos_almacen]
    pisos_options = [{"label": p, "value": p} for p in pisos]
    racks_options = [{"label": r, "value": r} for r in racks]
    letras_options = [{"label": l, "value": l} for l in letras]

    # Verificar si no hay posiciones disponibles
    if not tipos_almacen and not pisos and not racks and not letras:
        return (
            dbc.Alert(
                "No hay posiciones disponibles, cambie de ubicacion", color="warning"
            ),
            tipos_almacen_options,
            pisos_options,
            racks_options,
            letras_options,
        )

    if n_clicks:
        # Validar campos vacíos
        if not all([tipo_almacen, piso, rack, letra, pallet_id]):
            return (
                dbc.Alert(
                    "Por favor, complete todos los campos antes de asignar.",
                    color="danger",
                ),
                tipos_almacen_options,
                pisos_options,
                racks_options,
                letras_options,
            )

        # Intentar asignar el pallet
        mensaje = asignar_ubicacion(pallet_id, tipo_almacen, piso, rack, letra)

        # Retornar mensaje con éxito o error
        if "Error" in mensaje:
            return (
                dbc.Alert(mensaje, color="danger"),
                tipos_almacen_options,
                pisos_options,
                racks_options,
                letras_options,
            )

        return (
            dbc.Alert(mensaje, color="success"),
            tipos_almacen_options,
            pisos_options,
            racks_options,
            letras_options,
        )

    # Si no hay interacción, solo devuelve las opciones actualizadas
    return "", tipos_almacen_options, pisos_options, racks_options, letras_options

@app.callback(
    Output("liberar-feedback", "children"),
    Input("liberar-button", "n_clicks"),
    State("pallet-id-liberar", "value")
)
def handle_liberar_pallet(n_clicks, pallet_id):
    """Libera la ubicación del pallet especificado."""
    if n_clicks:
        if not pallet_id:
            return dbc.Alert("Ingrese el ID del pallet.", color="danger")
        mensaje = liberar_ubicacion(pallet_id)
        color = "success" if "Éxito" in mensaje else "danger"
        return dbc.Alert(mensaje, color=color)
    return ""

@app.callback(
    Output("create-user-modal", "is_open"),
    [Input("open-create-user-modal", "n_clicks"),
     Input("close-create-user-modal", "n_clicks")],
    [State("create-user-modal", "is_open")]
)
def toggle_create_user_modal(open_clicks, close_clicks, is_open):
    if open_clicks or close_clicks:
        return not is_open
    return is_open


@app.callback(
    [Output("login-feedback", "children"), Output("url", "pathname")],
    Input("login-button", "n_clicks"),
    [State("login-username", "value"), State("login-password", "value")],
    prevent_initial_call=True  # Evita que el callback se ejecute al cargar la página
)
def handle_login(n_clicks, username, password):
    """Maneja el inicio de sesión y valida las credenciales."""
    if n_clicks:
        # Verificar si los campos están vacíos
        if not username or not password:
            return dbc.Alert("Por favor, complete los campos de usuario y contraseña.", color="warning"), no_update

        # Validar las credenciales
        if verificar_credenciales(username, password):
            # Inicio de sesión exitoso, permite la redirección
            return "", "/gestion"

        # Credenciales incorrectas
        return dbc.Alert("Credenciales incorrectas. Por favor, intente de nuevo.", color="danger"), no_update

    # Estado inicial: sin interacción
    return "", no_update






@app.callback(
    [
        Output("new-username", "value"),  # Limpia el campo de nuevo usuario
        Output("new-password", "value"),  # Limpia el campo de nueva contraseña
        Output("create-user-feedback", "children"),  # Muestra el mensaje de feedback
    ],
    Input("create-user-button", "n_clicks"),
    State("new-username", "value"),
    State("new-password", "value"),
    prevent_initial_call=True  # Evita que el callback se dispare al cargar la página
)
def handle_create_user(n_clicks, username, password):
    """Maneja la creación de usuarios y limpia los campos si es exitoso."""
    if n_clicks:
        if username and password:
            resultado = crear_usuario(username, password)
            if resultado is True:
                # Usuario creado con éxito; limpia los campos y muestra feedback
                return "", "", dbc.Alert("Usuario creado exitosamente.", color="success")
            else:
                # Error al crear usuario; no limpia los campos
                return no_update, no_update, dbc.Alert("Error al crear usuario. Es posible que el usuario ya exista.", color="danger")
        # Campos incompletos
        return no_update, no_update, dbc.Alert("Por favor, complete todos los campos.", color="danger")
    # Retorno inicial (en teoría, no debería ejecutarse debido a prevent_initial_call)
    return no_update, no_update, ""





# --- Layout Inicial ---
app.layout = html.Div([
    dcc.Location(id="url", refresh=True),  # Maneja las redirecciones
    html.Div(id="page-content")  # Contenedor para el contenido de la página
])


# --- Ejecutar la Aplicación ---
if __name__ == "__main__":
    app.run_server(debug=True)