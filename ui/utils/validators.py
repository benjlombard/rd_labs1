"""
Utilitaires de validation
Fonctions pour valider les données et les entrées utilisateur
"""

import pandas as pd
import re
from datetime import datetime
from typing import Union, List, Optional, Tuple, Any


# =============================================================================
# VALIDATION DE DONNÉES DE BASE
# =============================================================================

def is_valid_number(
    value: Any,
    min_value: Optional[float] = None,
    max_value: Optional[float] = None
) -> bool:
    """
    Vérifie si une valeur est un nombre valide
    
    Args:
        value: Valeur à vérifier
        min_value: Valeur minimale autorisée
        max_value: Valeur maximale autorisée
    
    Returns:
        True si valide
    
    Example:
        >>> is_valid_number(42)
        True
        >>> is_valid_number(42, min_value=0, max_value=100)
        True
        >>> is_valid_number(150, max_value=100)
        False
    """
    try:
        num = float(value)
        
        if pd.isna(num):
            return False
        
        if min_value is not None and num < min_value:
            return False
        
        if max_value is not None and num > max_value:
            return False
        
        return True
    
    except (ValueError, TypeError):
        return False


def is_valid_integer(
    value: Any,
    min_value: Optional[int] = None,
    max_value: Optional[int] = None
) -> bool:
    """
    Vérifie si une valeur est un entier valide
    
    Args:
        value: Valeur à vérifier
        min_value: Valeur minimale
        max_value: Valeur maximale
    
    Returns:
        True si valide
    """
    try:
        num = int(value)
        
        if min_value is not None and num < min_value:
            return False
        
        if max_value is not None and num > max_value:
            return False
        
        return True
    
    except (ValueError, TypeError):
        return False


def is_valid_string(
    value: Any,
    min_length: Optional[int] = None,
    max_length: Optional[int] = None,
    allow_empty: bool = False
) -> bool:
    """
    Vérifie si une valeur est une chaîne valide
    
    Args:
        value: Valeur à vérifier
        min_length: Longueur minimale
        max_length: Longueur maximale
        allow_empty: Autoriser les chaînes vides
    
    Returns:
        True si valide
    
    Example:
        >>> is_valid_string("test")
        True
        >>> is_valid_string("", allow_empty=False)
        False
        >>> is_valid_string("abc", min_length=5)
        False
    """
    if pd.isna(value):
        return False
    
    text = str(value).strip()
    
    if not allow_empty and len(text) == 0:
        return False
    
    if min_length is not None and len(text) < min_length:
        return False
    
    if max_length is not None and len(text) > max_length:
        return False
    
    return True


def is_valid_date(
    value: Any,
    date_format: Optional[str] = None,
    min_date: Optional[datetime] = None,
    max_date: Optional[datetime] = None
) -> bool:
    """
    Vérifie si une valeur est une date valide
    
    Args:
        value: Valeur à vérifier
        date_format: Format attendu (None = auto)
        min_date: Date minimale
        max_date: Date maximale
    
    Returns:
        True si valide
    
    Example:
        >>> is_valid_date("2024-01-15")
        True
        >>> is_valid_date("15/01/2024", date_format="%d/%m/%Y")
        True
    """
    if pd.isna(value):
        return False
    
    try:
        if isinstance(value, (datetime, pd.Timestamp)):
            dt = value
        elif date_format:
            dt = datetime.strptime(str(value), date_format)
        else:
            dt = pd.to_datetime(value)
        
        if min_date and dt < min_date:
            return False
        
        if max_date and dt > max_date:
            return False
        
        return True
    
    except (ValueError, TypeError):
        return False


# =============================================================================
# VALIDATION DE FORMATS SPÉCIFIQUES
# =============================================================================

def is_valid_cas_id(cas_id: str) -> bool:
    """
    Vérifie si un CAS ID est valide
    
    Args:
        cas_id: CAS ID à vérifier
    
    Returns:
        True si valide
    
    Example:
        >>> is_valid_cas_id("7732-18-5")
        True
        >>> is_valid_cas_id("7732185")
        True
        >>> is_valid_cas_id("invalid")
        False
    """
    if pd.isna(cas_id):
        return False
    
    # Supprimer les tirets
    cas_clean = str(cas_id).replace("-", "")
    
    # Vérifier que ce sont bien des chiffres
    if not cas_clean.isdigit():
        return False
    
    # Vérifier la longueur (minimum 5 chiffres, maximum 10)
    if len(cas_clean) < 5 or len(cas_clean) > 10:
        return False
    
    # Optionnel: vérifier le checksum du CAS
    # Le dernier chiffre est un checksum calculé
    try:
        check_digit = int(cas_clean[-1])
        digits = [int(d) for d in cas_clean[:-1]]
        
        checksum = sum(d * (i + 1) for i, d in enumerate(reversed(digits))) % 10
        
        return checksum == check_digit
    
    except (ValueError, IndexError):
        return False


def is_valid_email(email: str) -> bool:
    """
    Vérifie si un email est valide
    
    Args:
        email: Email à vérifier
    
    Returns:
        True si valide
    
    Example:
        >>> is_valid_email("user@example.com")
        True
        >>> is_valid_email("invalid.email")
        False
    """
    if pd.isna(email):
        return False
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, str(email)))


def is_valid_url(url: str) -> bool:
    """
    Vérifie si une URL est valide
    
    Args:
        url: URL à vérifier
    
    Returns:
        True si valide
    
    Example:
        >>> is_valid_url("https://www.example.com")
        True
        >>> is_valid_url("not a url")
        False
    """
    if pd.isna(url):
        return False
    
    pattern = r'^https?://[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(/.*)?$'
    return bool(re.match(pattern, str(url)))


def is_valid_phone(phone: str, country: str = "FR") -> bool:
    """
    Vérifie si un numéro de téléphone est valide
    
    Args:
        phone: Numéro de téléphone
        country: Code pays
    
    Returns:
        True si valide
    
    Example:
        >>> is_valid_phone("0123456789", "FR")
        True
        >>> is_valid_phone("+33123456789", "FR")
        True
    """
    if pd.isna(phone):
        return False
    
    # Nettoyer le numéro
    phone_clean = re.sub(r'[^0-9+]', '', str(phone))
    
    if country == "FR":
        # Format français: 10 chiffres commençant par 0, ou +33 + 9 chiffres
        if phone_clean.startswith('+33'):
            return len(phone_clean) == 12
        else:
            return len(phone_clean) == 10 and phone_clean.startswith('0')
    
    # Validation générique: au moins 8 chiffres
    return len(phone_clean) >= 8


# =============================================================================
# VALIDATION DE DATAFRAMES
# =============================================================================

def validate_dataframe_columns(
    df: pd.DataFrame,
    required_columns: List[str]
) -> Tuple[bool, List[str]]:
    """
    Vérifie si un DataFrame contient les colonnes requises
    
    Args:
        df: DataFrame à vérifier
        required_columns: Liste des colonnes requises
    
    Returns:
        Tuple (est_valide, colonnes_manquantes)
    
    Example:
        >>> valid, missing = validate_dataframe_columns(df, ['cas_id', 'cas_name'])
        >>> if not valid:
        ...     print(f"Colonnes manquantes: {missing}")
    """
    missing = [col for col in required_columns if col not in df.columns]
    return len(missing) == 0, missing


def validate_dataframe_not_empty(df: pd.DataFrame) -> bool:
    """
    Vérifie si un DataFrame n'est pas vide
    
    Args:
        df: DataFrame à vérifier
    
    Returns:
        True si non vide
    """
    return not df.empty and len(df) > 0


def validate_column_type(
    df: pd.DataFrame,
    column: str,
    expected_type: type
) -> bool:
    """
    Vérifie le type d'une colonne
    
    Args:
        df: DataFrame
        column: Nom de la colonne
        expected_type: Type attendu
    
    Returns:
        True si le type correspond
    
    Example:
        >>> validate_column_type(df, 'risk_score', float)
        True
    """
    if column not in df.columns:
        return False
    
    try:
        return df[column].dtype == expected_type or pd.api.types.is_dtype_equal(df[column].dtype, expected_type)
    except Exception:
        return False


def validate_no_duplicates(
    df: pd.DataFrame,
    columns: Optional[List[str]] = None
) -> Tuple[bool, pd.DataFrame]:
    """
    Vérifie l'absence de doublons
    
    Args:
        df: DataFrame à vérifier
        columns: Colonnes à considérer (None = toutes)
    
    Returns:
        Tuple (pas_de_doublons, dataframe_des_doublons)
    
    Example:
        >>> valid, duplicates = validate_no_duplicates(df, ['cas_id'])
        >>> if not valid:
        ...     print(f"{len(duplicates)} doublons trouvés")
    """
    if columns:
        duplicates = df[df.duplicated(subset=columns, keep=False)]
    else:
        duplicates = df[df.duplicated(keep=False)]
    
    return len(duplicates) == 0, duplicates


def validate_column_values(
    df: pd.DataFrame,
    column: str,
    allowed_values: List[Any]
) -> Tuple[bool, List[Any]]:
    """
    Vérifie que les valeurs d'une colonne sont dans une liste autorisée
    
    Args:
        df: DataFrame
        column: Nom de la colonne
        allowed_values: Valeurs autorisées
    
    Returns:
        Tuple (est_valide, valeurs_invalides)
    
    Example:
        >>> valid, invalid = validate_column_values(
        ...     df,
        ...     'risk_level',
        ...     ['Faible', 'Moyen', 'Élevé', 'Critique']
        ... )
    """
    if column not in df.columns:
        return False, []
    
    invalid_values = df[~df[column].isin(allowed_values)][column].unique().tolist()
    
    return len(invalid_values) == 0, invalid_values


# =============================================================================
# VALIDATION DE PLAGES
# =============================================================================

def is_in_range(
    value: Union[int, float],
    min_value: Union[int, float],
    max_value: Union[int, float],
    inclusive: bool = True
) -> bool:
    """
    Vérifie si une valeur est dans une plage
    
    Args:
        value: Valeur à vérifier
        min_value: Valeur minimale
        max_value: Valeur maximale
        inclusive: Inclure les bornes
    
    Returns:
        True si dans la plage
    
    Example:
        >>> is_in_range(50, 0, 100)
        True
        >>> is_in_range(100, 0, 100, inclusive=False)
        False
    """
    try:
        val = float(value)
        
        if inclusive:
            return min_value <= val <= max_value
        else:
            return min_value < val < max_value
    
    except (ValueError, TypeError):
        return False


def validate_percentage(value: Union[int, float]) -> bool:
    """
    Vérifie si une valeur est un pourcentage valide (0-100)
    
    Args:
        value: Valeur à vérifier
    
    Returns:
        True si valide
    """
    return is_in_range(value, 0, 100)


def validate_risk_score(score: Union[int, float]) -> bool:
    """
    Vérifie si un score de risque est valide (0-100)
    
    Args:
        score: Score à vérifier
    
    Returns:
        True si valide
    """
    return is_in_range(score, 0, 100)


# =============================================================================
# VALIDATION DE FICHIERS
# =============================================================================

def validate_file_extension(
    filename: str,
    allowed_extensions: List[str]
) -> bool:
    """
    Vérifie l'extension d'un fichier
    
    Args:
        filename: Nom du fichier
        allowed_extensions: Extensions autorisées (avec ou sans point)
    
    Returns:
        True si valide
    
    Example:
        >>> validate_file_extension("data.xlsx", [".xlsx", ".xls"])
        True
        >>> validate_file_extension("data.txt", ["xlsx", "xls"])
        False
    """
    if pd.isna(filename):
        return False
    
    # Normaliser les extensions
    exts = [ext if ext.startswith('.') else f'.{ext}' for ext in allowed_extensions]
    
    # Vérifier
    filename_lower = str(filename).lower()
    return any(filename_lower.endswith(ext.lower()) for ext in exts)


def validate_file_size(
    size_bytes: int,
    max_size_mb: float
) -> bool:
    """
    Vérifie la taille d'un fichier
    
    Args:
        size_bytes: Taille en bytes
        max_size_mb: Taille maximale en MB
    
    Returns:
        True si valide
    
    Example:
        >>> validate_file_size(5242880, 10)  # 5 MB < 10 MB
        True
    """
    max_size_bytes = max_size_mb * 1024 * 1024
    return size_bytes <= max_size_bytes


# =============================================================================
# SANITIZATION
# =============================================================================

def sanitize_string(text: str, max_length: Optional[int] = None) -> str:
    """
    Nettoie une chaîne de caractères
    
    Args:
        text: Texte à nettoyer
        max_length: Longueur maximale
    
    Returns:
        Texte nettoyé
    
    Example:
        >>> sanitize_string("  Hello World!  ")
        'Hello World!'
    """
    if pd.isna(text):
        return ""
    
    # Convertir en string et trim
    cleaned = str(text).strip()
    
    # Supprimer les caractères de contrôle
    cleaned = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', cleaned)
    
    # Tronquer si nécessaire
    if max_length and len(cleaned) > max_length:
        cleaned = cleaned[:max_length]
    
    return cleaned


def sanitize_filename(filename: str) -> str:
    """
    Nettoie un nom de fichier
    
    Args:
        filename: Nom de fichier
    
    Returns:
        Nom nettoyé
    
    Example:
        >>> sanitize_filename("my/file<name>.txt")
        'my_file_name_.txt'
    """
    if pd.isna(filename):
        return "untitled"
    
    # Remplacer les caractères interdits
    cleaned = re.sub(r'[<>:"/\\|?*]', '_', str(filename))
    
    # Supprimer les espaces multiples
    cleaned = re.sub(r'\s+', ' ', cleaned)
    
    return cleaned.strip()


# =============================================================================
# VALIDATION COMPLEXE
# =============================================================================

def validate_data_integrity(
    df: pd.DataFrame,
    rules: dict
) -> Tuple[bool, List[str]]:
    """
    Valide l'intégrité des données selon des règles
    
    Args:
        df: DataFrame à valider
        rules: Dict de règles de validation
    
    Returns:
        Tuple (est_valide, liste_erreurs)
    
    Example:
        >>> rules = {
        ...     'required_columns': ['cas_id', 'cas_name'],
        ...     'unique_columns': ['cas_id'],
        ...     'non_null_columns': ['cas_name']
        ... }
        >>> valid, errors = validate_data_integrity(df, rules)
    """
    errors = []
    
    # Vérifier les colonnes requises
    if 'required_columns' in rules:
        valid, missing = validate_dataframe_columns(df, rules['required_columns'])
        if not valid:
            errors.append(f"Colonnes manquantes: {', '.join(missing)}")
    
    # Vérifier les doublons
    if 'unique_columns' in rules:
        for col in rules['unique_columns']:
            if col in df.columns:
                valid, duplicates = validate_no_duplicates(df, [col])
                if not valid:
                    errors.append(f"Doublons trouvés dans {col}: {len(duplicates)} lignes")
    
    # Vérifier les valeurs non nulles
    if 'non_null_columns' in rules:
        for col in rules['non_null_columns']:
            if col in df.columns:
                null_count = df[col].isna().sum()
                if null_count > 0:
                    errors.append(f"Valeurs nulles dans {col}: {null_count} lignes")
    
    return len(errors) == 0, errors