priorities = {
    1: [  # Baja
        "Cambio de Contraseña en Router Wifi",
        "Cambio de Domicilio",
        "Recolección De Equipos",
        "Cancelación",
        "Desconexión"
    ],
    2: [  # Normal
        "Internet Lento",
        "Internet Intermitente",
        "Antena Desalineada",
        "Cables Mal Colocados",
        "Cableado Para Modem Extra"
    ],
    3: [  # Alta
        "No Tiene Internet",
        "Antena Dañada",
        "No Responde la Antena",
        "No Responde el Router Wifi",
        "Router Wifi Reseteado (Valores de Fabrica)",
        "Cambio de Router Wifi",
        "Cambio de Antena",
        "Cambio de Antena + Router Wifi",
        "Cable UTP Dañado",
        "PoE Dañado",
        "Conector Dañado",
        "Antena valores De Fabrica",
        "Eliminador Dañado",
        "RJ45 Dañado",
        "Alambres Rotos",
        "Reconexión",
        "Cable Fibra Dañado",
        "Jumper Dañado"
    ],
    4: [  # Muy Alta
        "Troncal Dañado",
        "Caja Nap Dañada",
        "Cambio A Fibra Óptica"
    ]
}

def get_priority(subject):
    for priority, subjects in priorities.items():
        if subject in subjects:
            return priority
    return None