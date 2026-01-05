"""
Utilitaires de formatage
Fonctions pour formater les données pour l'affichage
"""

import pandas as pd
from datetime import datetime, timedelta
from typing import Union, Optional, List, Any


# =============================================================================
# FORMATAGE DE NOMBRES
# =============================================================================

def format_number(
    value: Union[int, float],
    decimals: int = 0,
    thousands_sep: str = " ",
    decimal_sep: str = ",",
    prefix: str = "",
    suffix: str = ""
) -> str:
    """
    Formate un nombre avec séparateurs
    
    Args:
        value: Nombre à formater
        decimals: Nombre de décimales
        thousands_sep: Séparateur des milliers
        decimal_sep: Séparateur décimal
        prefix: Préfixe (ex: "€")
        suffix: Suffixe (ex: "%")
    
    Returns:
        Nombre formaté
    
    Example:
        >>> format_number(1234567.89, decimals=2)
        '1 234 567,89'
        >>> format_number(1500, prefix="€", suffix=" EUR")
        '€1 500 EUR'
    """
    if pd.isna(value):
        return "N/A"
    
    try:
        if decimals == 0:
            formatted = f"{int(value):,}".replace(",", thousands_sep)
        else:
            formatted = f"{float(value):,.{decimals}f}"
            formatted = formatted.replace(",", "TEMP")
            formatted = formatted.replace(".", decimal_sep)
            formatted = formatted.replace("TEMP", thousands_sep)
        
        return f"{prefix}{formatted}{suffix}"
    
    except (ValueError, TypeError):
        return str(value)


def format_percentage(
    value: Union[int, float],
    decimals: int = 1,
    multiply: bool = True
) -> str:
    """
    Formate un nombre en pourcentage
    
    Args:
        value: Valeur à formater
        decimals: Nombre de décimales
        multiply: Si True, multiplie par 100
    
    Returns:
        Pourcentage formaté
    
    Example:
        >>> format_percentage(0.156, decimals=1)
        '15,6%'
        >>> format_percentage(45.6, multiply=False)
        '45,6%'
    """
    if pd.isna(value):
        return "N/A"
    
    try:
        val = float(value)
        if multiply:
            val *= 100
        
        return format_number(val, decimals=decimals, suffix="%")
    
    except (ValueError, TypeError):
        return str(value)


def format_currency(
    value: Union[int, float],
    currency: str = "€",
    decimals: int = 2,
    position: str = "prefix"
) -> str:
    """
    Formate un montant monétaire
    
    Args:
        value: Montant
        currency: Symbole de devise
        decimals: Nombre de décimales
        position: 'prefix' ou 'suffix'
    
    Returns:
        Montant formaté
    
    Example:
        >>> format_currency(1234.56)
        '€1 234,56'
        >>> format_currency(1234.56, currency="USD", position="suffix")
        '1 234,56 USD'
    """
    if pd.isna(value):
        return "N/A"
    
    if position == "prefix":
        return format_number(value, decimals=decimals, prefix=currency)
    else:
        return format_number(value, decimals=decimals, suffix=f" {currency}")


def format_large_number(value: Union[int, float], precision: int = 1) -> str:
    """
    Formate les grands nombres avec K, M, B
    
    Args:
        value: Nombre à formater
        precision: Précision
    
    Returns:
        Nombre formaté
    
    Example:
        >>> format_large_number(1234)
        '1,2K'
        >>> format_large_number(1234567)
        '1,2M'
        >>> format_large_number(1234567890)
        '1,2B'
    """
    if pd.isna(value):
        return "N/A"
    
    try:
        val = float(value)
        
        if abs(val) >= 1_000_000_000:
            return f"{val/1_000_000_000:.{precision}f}B".replace(".", ",")
        elif abs(val) >= 1_000_000:
            return f"{val/1_000_000:.{precision}f}M".replace(".", ",")
        elif abs(val) >= 1_000:
            return f"{val/1_000:.{precision}f}K".replace(".", ",")
        else:
            return format_number(val, decimals=precision)
    
    except (ValueError, TypeError):
        return str(value)


# =============================================================================
# FORMATAGE DE DATES
# =============================================================================

def format_date(
    date: Union[str, datetime, pd.Timestamp],
    format_string: str = "%d/%m/%Y"
) -> str:
    """
    Formate une date
    
    Args:
        date: Date à formater
        format_string: Format de sortie
    
    Returns:
        Date formatée
    
    Example:
        >>> format_date("2024-01-15")
        '15/01/2024'
        >>> format_date(datetime.now(), "%d %B %Y")
        '01 janvier 2024'
    """
    if pd.isna(date):
        return "N/A"
    
    try:
        if isinstance(date, str):
            date = pd.to_datetime(date)
        
        return date.strftime(format_string)
    
    except (ValueError, AttributeError):
        return str(date)


def format_datetime(
    dt: Union[str, datetime, pd.Timestamp],
    format_string: str = "%d/%m/%Y %H:%M"
) -> str:
    """
    Formate une date et heure
    
    Args:
        dt: DateTime à formater
        format_string: Format de sortie
    
    Returns:
        DateTime formaté
    
    Example:
        >>> format_datetime("2024-01-15 14:30:00")
        '15/01/2024 14:30'
    """
    return format_date(dt, format_string)


def format_relative_date(date: Union[str, datetime, pd.Timestamp]) -> str:
    """
    Formate une date de façon relative (il y a X jours)
    
    Args:
        date: Date à formater
    
    Returns:
        Date relative
    
    Example:
        >>> format_relative_date(datetime.now() - timedelta(days=2))
        'Il y a 2 jours'
        >>> format_relative_date(datetime.now() - timedelta(hours=3))
        'Il y a 3 heures'
    """
    if pd.isna(date):
        return "N/A"
    
    try:
        if isinstance(date, str):
            date = pd.to_datetime(date)
        
        now = datetime.now()
        diff = now - date
        
        seconds = diff.total_seconds()
        
        if seconds < 60:
            return "À l'instant"
        elif seconds < 3600:
            minutes = int(seconds / 60)
            return f"Il y a {minutes} minute{'s' if minutes > 1 else ''}"
        elif seconds < 86400:
            hours = int(seconds / 3600)
            return f"Il y a {hours} heure{'s' if hours > 1 else ''}"
        elif seconds < 604800:
            days = int(seconds / 86400)
            return f"Il y a {days} jour{'s' if days > 1 else ''}"
        elif seconds < 2592000:
            weeks = int(seconds / 604800)
            return f"Il y a {weeks} semaine{'s' if weeks > 1 else ''}"
        elif seconds < 31536000:
            months = int(seconds / 2592000)
            return f"Il y a {months} mois"
        else:
            years = int(seconds / 31536000)
            return f"Il y a {years} an{'s' if years > 1 else ''}"
    
    except (ValueError, AttributeError, TypeError):
        return str(date)


def format_duration(seconds: Union[int, float]) -> str:
    """
    Formate une durée en secondes
    
    Args:
        seconds: Durée en secondes
    
    Returns:
        Durée formatée
    
    Example:
        >>> format_duration(3665)
        '1h 1m 5s'
        >>> format_duration(125)
        '2m 5s'
    """
    if pd.isna(seconds):
        return "N/A"
    
    try:
        seconds = int(seconds)
        
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        
        parts = []
        if hours > 0:
            parts.append(f"{hours}h")
        if minutes > 0:
            parts.append(f"{minutes}m")
        if secs > 0 or not parts:
            parts.append(f"{secs}s")
        
        return " ".join(parts)
    
    except (ValueError, TypeError):
        return str(seconds)


# =============================================================================
# FORMATAGE DE TEXTE
# =============================================================================

def format_cas_id(cas_id: str) -> str:
    """
    Formate un CAS ID (XXX-XX-X)
    
    Args:
        cas_id: CAS ID à formater
    
    Returns:
        CAS ID formaté
    
    Example:
        >>> format_cas_id("7732185")
        '7732-18-5'
    """
    if pd.isna(cas_id):
        return "N/A"
    
    try:
        cas_str = str(cas_id).replace("-", "")
        
        if len(cas_str) >= 5:
            return f"{cas_str[:-3]}-{cas_str[-3:-1]}-{cas_str[-1]}"
        else:
            return cas_str
    
    except Exception:
        return str(cas_id)


def truncate_text(
    text: str,
    max_length: int = 50,
    suffix: str = "..."
) -> str:
    """
    Tronque un texte à une longueur maximale
    
    Args:
        text: Texte à tronquer
        max_length: Longueur maximale
        suffix: Suffixe à ajouter si tronqué
    
    Returns:
        Texte tronqué
    
    Example:
        >>> truncate_text("Ceci est un très long texte", 15)
        'Ceci est un ...'
    """
    if pd.isna(text):
        return ""
    
    text = str(text)
    
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def capitalize_first(text: str) -> str:
    """
    Met en majuscule la première lettre
    
    Args:
        text: Texte à formater
    
    Returns:
        Texte formaté
    
    Example:
        >>> capitalize_first("bonjour le monde")
        'Bonjour le monde'
    """
    if pd.isna(text) or not text:
        return ""
    
    text = str(text)
    return text[0].upper() + text[1:] if len(text) > 0 else text


def format_list(items: List[Any], separator: str = ", ", max_items: int = None) -> str:
    """
    Formate une liste en texte
    
    Args:
        items: Liste d'éléments
        separator: Séparateur
        max_items: Nombre maximum d'éléments à afficher
    
    Returns:
        Liste formatée
    
    Example:
        >>> format_list(['A', 'B', 'C', 'D'], max_items=3)
        'A, B, C (+1 autre)'
    """
    if not items:
        return ""
    
    items_str = [str(item) for item in items if not pd.isna(item)]
    
    if max_items and len(items_str) > max_items:
        displayed = items_str[:max_items]
        remaining = len(items_str) - max_items
        return separator.join(displayed) + f" (+{remaining} autre{'s' if remaining > 1 else ''})"
    
    return separator.join(items_str)


# =============================================================================
# FORMATAGE DE DATAFRAMES
# =============================================================================

def format_dataframe_column(
    df: pd.DataFrame,
    column: str,
    formatter: Union[str, callable]
) -> pd.DataFrame:
    """
    Formate une colonne de DataFrame
    
    Args:
        df: DataFrame
        column: Nom de la colonne
        formatter: Format string ou fonction
    
    Returns:
        DataFrame avec colonne formatée
    
    Example:
        >>> df = format_dataframe_column(df, 'price', lambda x: format_currency(x))
        >>> df = format_dataframe_column(df, 'date', '%d/%m/%Y')
    """
    if column not in df.columns:
        return df
    
    df_copy = df.copy()
    
    if callable(formatter):
        df_copy[column] = df_copy[column].apply(formatter)
    elif isinstance(formatter, str):
        # Assume datetime format
        df_copy[column] = pd.to_datetime(df_copy[column], errors='coerce').dt.strftime(formatter)
    
    return df_copy


def format_dataframe_for_display(
    df: pd.DataFrame,
    date_columns: Optional[List[str]] = None,
    number_columns: Optional[List[str]] = None,
    percentage_columns: Optional[List[str]] = None,
    currency_columns: Optional[List[str]] = None,
    date_format: str = "%d/%m/%Y",
    number_decimals: int = 2
) -> pd.DataFrame:
    """
    Formate un DataFrame complet pour l'affichage
    
    Args:
        df: DataFrame à formater
        date_columns: Colonnes de dates
        number_columns: Colonnes numériques
        percentage_columns: Colonnes de pourcentages
        currency_columns: Colonnes monétaires
        date_format: Format des dates
        number_decimals: Décimales pour les nombres
    
    Returns:
        DataFrame formaté
    
    Example:
        >>> formatted = format_dataframe_for_display(
        ...     df,
        ...     date_columns=['created_at'],
        ...     number_columns=['score'],
        ...     percentage_columns=['completion'],
        ...     currency_columns=['price']
        ... )
    """
    df_formatted = df.copy()
    
    # Dates
    if date_columns:
        for col in date_columns:
            if col in df_formatted.columns:
                df_formatted[col] = df_formatted[col].apply(
                    lambda x: format_date(x, date_format)
                )
    
    # Nombres
    if number_columns:
        for col in number_columns:
            if col in df_formatted.columns:
                df_formatted[col] = df_formatted[col].apply(
                    lambda x: format_number(x, decimals=number_decimals)
                )
    
    # Pourcentages
    if percentage_columns:
        for col in percentage_columns:
            if col in df_formatted.columns:
                df_formatted[col] = df_formatted[col].apply(
                    lambda x: format_percentage(x, multiply=False)
                )
    
    # Devises
    if currency_columns:
        for col in currency_columns:
            if col in df_formatted.columns:
                df_formatted[col] = df_formatted[col].apply(format_currency)
    
    return df_formatted


# =============================================================================
# FORMATAGE SPÉCIALISÉ
# =============================================================================

def format_risk_level(level: str) -> str:
    """
    Formate un niveau de risque avec emoji
    
    Args:
        level: Niveau de risque
    
    Returns:
        Niveau formaté avec emoji
    
    Example:
        >>> format_risk_level("Critique")
        '🔴 Critique'
    """
    if pd.isna(level):
        return "⚪ N/A"
    
    level_lower = str(level).lower()
    
    emoji_map = {
        'critique': '🔴',
        'élevé': '🟠',
        'moyen': '🟡',
        'faible': '🟢',
        'très faible': '⚪'
    }
    
    for key, emoji in emoji_map.items():
        if key in level_lower:
            return f"{emoji} {level}"
    
    return str(level)


def format_change_type(change_type: str) -> str:
    """
    Formate un type de changement avec emoji
    
    Args:
        change_type: Type de changement
    
    Returns:
        Type formaté avec emoji
    
    Example:
        >>> format_change_type("insertion")
        '✅ Insertion'
    """
    if pd.isna(change_type):
        return "N/A"
    
    type_lower = str(change_type).lower()
    
    if 'insertion' in type_lower or 'insert' in type_lower:
        return f"✅ {change_type.capitalize()}"
    elif 'deletion' in type_lower or 'delete' in type_lower or 'suppression' in type_lower:
        return f"❌ {change_type.capitalize()}"
    elif 'modification' in type_lower or 'modify' in type_lower:
        return f"✏️ {change_type.capitalize()}"
    else:
        return str(change_type)


def format_file_size(size_bytes: Union[int, float]) -> str:
    """
    Formate une taille de fichier
    
    Args:
        size_bytes: Taille en bytes
    
    Returns:
        Taille formatée
    
    Example:
        >>> format_file_size(1536)
        '1,5 KB'
        >>> format_file_size(1048576)
        '1,0 MB'
    """
    if pd.isna(size_bytes):
        return "N/A"
    
    try:
        size = float(size_bytes)
        
        if size < 1024:
            return f"{size:.0f} B"
        elif size < 1024 ** 2:
            return f"{size/1024:.1f} KB".replace(".", ",")
        elif size < 1024 ** 3:
            return f"{size/(1024**2):.1f} MB".replace(".", ",")
        else:
            return f"{size/(1024**3):.1f} GB".replace(".", ",")
    
    except (ValueError, TypeError):
        return str(size_bytes)