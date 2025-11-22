# -*- coding: utf-8 -*-
"""
ARGO v8.5.4 - Excel Analysis Module
Capacidades avanzadas de análisis de hojas de cálculo
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Union, Any
import json
from datetime import datetime


class ExcelAnalyzer:
    """Analizador avanzado de archivos Excel con capacidades de cálculo"""
    
    def __init__(self):
        self.current_workbook = None
        self.sheets = {}
        self.metadata = {}
        
    def load_excel(self, filepath: Union[str, Path]) -> Dict[str, Any]:
        """
        Carga un archivo Excel y extrae toda la información
        
        Args:
            filepath: Ruta al archivo Excel
            
        Returns:
            Dict con información del archivo y sus hojas
        """
        try:
            filepath = Path(filepath)
            
            # Cargar todas las hojas
            excel_file = pd.ExcelFile(filepath)
            
            self.metadata = {
                'filename': filepath.name,
                'sheets': excel_file.sheet_names,
                'loaded_at': datetime.now().isoformat()
            }
            
            # Cargar cada hoja
            for sheet_name in excel_file.sheet_names:
                df = pd.read_excel(filepath, sheet_name=sheet_name, header=None)
                self.sheets[sheet_name] = df
            
            # Análisis inicial
            analysis = self.analyze_workbook()
            
            return {
                'status': 'success',
                'metadata': self.metadata,
                'analysis': analysis
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def analyze_workbook(self) -> Dict[str, Any]:
        """Analiza el workbook completo"""
        analysis = {}
        
        for sheet_name, df in self.sheets.items():
            analysis[sheet_name] = self.analyze_sheet(df, sheet_name)
        
        return analysis
    
    def analyze_sheet(self, df: pd.DataFrame, sheet_name: str) -> Dict[str, Any]:
        """
        Analiza una hoja específica
        
        Returns:
            Dict con análisis detallado de la hoja
        """
        # Detectar encabezados probables
        header_row = self._detect_headers(df)
        
        if header_row is not None:
            # Re-cargar con headers
            df.columns = df.iloc[header_row]
            df = df[header_row + 1:].reset_index(drop=True)
        
        analysis = {
            'dimensions': {
                'rows': len(df),
                'columns': len(df.columns)
            },
            'columns': list(df.columns),
            'data_types': self._analyze_data_types(df),
            'summary_stats': self._get_summary_stats(df),
            'formulas_detected': self._detect_formulas(df),
            'empty_cells': self._count_empty_cells(df),
            'header_row': header_row
        }
        
        return analysis
    
    def _detect_headers(self, df: pd.DataFrame) -> Optional[int]:
        """Detecta automáticamente la fila de encabezados"""
        for i in range(min(10, len(df))):
            row = df.iloc[i]
            # Si la mayoría de celdas son strings y no están vacías
            non_null = row.dropna()
            if len(non_null) > len(df.columns) * 0.5:
                if all(isinstance(x, str) for x in non_null):
                    return i
        return None
    
    def _analyze_data_types(self, df: pd.DataFrame) -> Dict[str, str]:
        """Analiza los tipos de datos en cada columna"""
        types = {}
        for col in df.columns:
            if df[col].dtype == 'object':
                # Verificar si son fechas, números como strings, etc.
                sample = df[col].dropna().head(100)
                if self._is_date_column(sample):
                    types[str(col)] = 'date'
                elif self._is_numeric_string(sample):
                    types[str(col)] = 'numeric_string'
                else:
                    types[str(col)] = 'text'
            elif np.issubdtype(df[col].dtype, np.number):
                types[str(col)] = 'numeric'
            elif np.issubdtype(df[col].dtype, np.datetime64):
                types[str(col)] = 'datetime'
            else:
                types[str(col)] = str(df[col].dtype)
        
        return types
    
    def _is_date_column(self, series) -> bool:
        """Verifica si una columna contiene fechas"""
        try:
            pd.to_datetime(series, errors='coerce')
            return True
        except:
            return False
    
    def _is_numeric_string(self, series) -> bool:
        """Verifica si una columna contiene números como strings"""
        try:
            pd.to_numeric(series, errors='coerce')
            return True
        except:
            return False
    
    def _get_summary_stats(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Obtiene estadísticas resumidas de columnas numéricas"""
        stats = {}
        
        for col in df.columns:
            if np.issubdtype(df[col].dtype, np.number):
                stats[str(col)] = {
                    'mean': float(df[col].mean()) if not df[col].isna().all() else None,
                    'median': float(df[col].median()) if not df[col].isna().all() else None,
                    'min': float(df[col].min()) if not df[col].isna().all() else None,
                    'max': float(df[col].max()) if not df[col].isna().all() else None,
                    'sum': float(df[col].sum()) if not df[col].isna().all() else None,
                    'count': int(df[col].count())
                }
        
        return stats
    
    def _detect_formulas(self, df: pd.DataFrame) -> List[str]:
        """Detecta celdas que podrían contener fórmulas"""
        formulas = []
        
        for col in df.columns:
            for idx, val in df[col].items():
                if isinstance(val, str) and val.startswith('='):
                    cell_ref = f"{col}{idx+2}"  # +2 porque Excel empieza en 1 y puede haber header
                    formulas.append(cell_ref)
        
        return formulas
    
    def _count_empty_cells(self, df: pd.DataFrame) -> Dict[str, int]:
        """Cuenta celdas vacías por columna"""
        empty = {}
        for col in df.columns:
            empty[str(col)] = int(df[col].isna().sum())
        return empty
    
    def get_cell_value(self, sheet: str, cell: str) -> Any:
        """
        Obtiene el valor de una celda específica
        
        Args:
            sheet: Nombre de la hoja
            cell: Referencia de celda (ej: 'A1', 'B5')
        """
        if sheet not in self.sheets:
            return None
        
        df = self.sheets[sheet]
        
        # Convertir referencia Excel a índices
        col_letter = ''.join(c for c in cell if c.isalpha())
        row_num = int(''.join(c for c in cell if c.isdigit())) - 1
        
        # Convertir letra a número de columna
        col_num = 0
        for i, char in enumerate(reversed(col_letter.upper())):
            col_num += (ord(char) - ord('A') + 1) * (26 ** i)
        col_num -= 1
        
        try:
            return df.iloc[row_num, col_num]
        except:
            return None
    
    def get_range_values(self, sheet: str, start_cell: str, end_cell: str) -> pd.DataFrame:
        """
        Obtiene valores de un rango de celdas
        
        Args:
            sheet: Nombre de la hoja
            start_cell: Celda inicial (ej: 'A1')
            end_cell: Celda final (ej: 'C10')
        """
        if sheet not in self.sheets:
            return pd.DataFrame()
        
        df = self.sheets[sheet]
        
        # Convertir referencias a índices
        start_col_letter = ''.join(c for c in start_cell if c.isalpha())
        start_row = int(''.join(c for c in start_cell if c.isdigit())) - 1
        
        end_col_letter = ''.join(c for c in end_cell if c.isalpha())
        end_row = int(''.join(c for c in end_cell if c.isdigit())) - 1
        
        # Convertir letras a números
        start_col = sum((ord(char) - ord('A') + 1) * (26 ** i) 
                        for i, char in enumerate(reversed(start_col_letter.upper()))) - 1
        end_col = sum((ord(char) - ord('A') + 1) * (26 ** i) 
                      for i, char in enumerate(reversed(end_col_letter.upper()))) - 1
        
        try:
            return df.iloc[start_row:end_row+1, start_col:end_col+1]
        except:
            return pd.DataFrame()
    
    def calculate(self, sheet: str, operation: str, range_or_column: str) -> float:
        """
        Realiza cálculos sobre columnas o rangos
        
        Args:
            sheet: Nombre de la hoja
            operation: 'sum', 'avg', 'min', 'max', 'count'
            range_or_column: Columna ('A') o rango ('A1:A10')
        """
        if sheet not in self.sheets:
            return 0.0
        
        df = self.sheets[sheet]
        
        # Determinar si es columna o rango
        if ':' in range_or_column:
            # Es un rango
            parts = range_or_column.split(':')
            data = self.get_range_values(sheet, parts[0], parts[1])
            values = data.values.flatten()
        else:
            # Es una columna
            if range_or_column.isalpha():
                col_num = sum((ord(char) - ord('A') + 1) * (26 ** i) 
                             for i, char in enumerate(reversed(range_or_column.upper()))) - 1
                values = df.iloc[:, col_num].values
            else:
                values = df[range_or_column].values if range_or_column in df.columns else []
        
        # Filtrar valores numéricos
        numeric_values = [v for v in values if pd.notna(v) and isinstance(v, (int, float))]
        
        if not numeric_values:
            return 0.0
        
        operations = {
            'sum': sum,
            'avg': lambda x: sum(x) / len(x),
            'mean': lambda x: sum(x) / len(x),
            'min': min,
            'max': max,
            'count': len
        }
        
        operation_func = operations.get(operation.lower(), sum)
        return float(operation_func(numeric_values))
    
    def find_values(self, sheet: str, search_value: Any) -> List[str]:
        """
        Busca un valor específico en una hoja
        
        Returns:
            Lista de referencias de celdas donde se encontró el valor
        """
        if sheet not in self.sheets:
            return []
        
        df = self.sheets[sheet]
        locations = []
        
        for col_idx, col in enumerate(df.columns):
            for row_idx, val in df[col].items():
                if val == search_value or str(val) == str(search_value):
                    # Convertir a referencia Excel
                    col_letter = ''
                    col_num = col_idx
                    while col_num >= 0:
                        col_letter = chr(col_num % 26 + ord('A')) + col_letter
                        col_num = col_num // 26 - 1
                    
                    cell_ref = f"{col_letter}{row_idx + 1}"
                    locations.append(cell_ref)
        
        return locations
    
    def export_summary(self) -> str:
        """
        Exporta un resumen textual del análisis
        
        Returns:
            Resumen formateado como string
        """
        if not self.sheets:
            return "No hay archivo Excel cargado"
        
        summary = f"ANÁLISIS DE EXCEL: {self.metadata.get('filename', 'archivo.xlsx')}\n"
        summary += "=" * 50 + "\n\n"
        
        for sheet_name, df in self.sheets.items():
            analysis = self.analyze_sheet(df, sheet_name)
            
            summary += f"HOJA: {sheet_name}\n"
            summary += f"• Dimensiones: {analysis['dimensions']['rows']} filas × {analysis['dimensions']['columns']} columnas\n"
            
            if analysis['summary_stats']:
                summary += "• Estadísticas numéricas:\n"
                for col, stats in analysis['summary_stats'].items():
                    if stats['count'] > 0:
                        summary += f"  - {col}: suma={stats['sum']:.2f}, promedio={stats['mean']:.2f}, min={stats['min']:.2f}, max={stats['max']:.2f}\n"
            
            if analysis['formulas_detected']:
                summary += f"• Fórmulas detectadas en: {', '.join(analysis['formulas_detected'][:5])}\n"
            
            summary += "\n"
        
        return summary


# Función auxiliar para integración con ARGO
def analyze_excel_for_rag(filepath: Union[str, Path]) -> str:
    """
    Analiza un archivo Excel y retorna texto para indexación en RAG
    
    Args:
        filepath: Ruta al archivo Excel
        
    Returns:
        String con el análisis formateado para RAG
    """
    analyzer = ExcelAnalyzer()
    result = analyzer.load_excel(filepath)
    
    if result['status'] == 'success':
        return analyzer.export_summary()
    else:
        return f"Error analizando Excel: {result.get('error', 'desconocido')}"
