# code/src/data_handler.py

# Python Libraries
import os
import pandas as pd
from pandas import DataFrame
from pandas.io.parsers import TextFileReader

# Local Libraries
from src.constants import (
    CLAIMS_FILE,
    EVIDENCE_REQ_FILE,
    OUTPUT_FILE,
    SAMPLE_CLAIMS_FILE,
    USER_HISTORY_FILE
)

class DataHandler:
    def __init__(self):
        self.claims = pd.DataFrame()
        self.evidence_reqs = pd.DataFrame()
        self.output = pd.DataFrame()
        self.user_history = pd.DataFrame()
        self._loaded_type = None  # Track state to avoid redundant I/O cycles

    def load_data(self, args: dict) -> None:
        """
        Loads the core data frames required for processing.
        Allows safe execution reloading between production and evaluation sample files.
        """
        target_type = "sample" if args.get("sample") else "production"

        # Guard clause: Skip repetitive parsing if data state has not changed
        if self._loaded_type == target_type and not self.claims.empty:
            return

        filepath = SAMPLE_CLAIMS_FILE if target_type == "sample" else CLAIMS_FILE

        self._load_claims(filepath)
        self._load_evidence_reqs(EVIDENCE_REQ_FILE)
        self._load_output(OUTPUT_FILE)
        self._load_user_history(USER_HISTORY_FILE)

        self._loaded_type = target_type

    def _safe_read_csv(self, file_path: str) -> DataFrame | TextFileReader:
        """Helper matrix wrapper to capture environmental system path errors cleanly."""
        if not os.path.exists(file_path):
            print(f"⚠️ Warning: Target file path target '{file_path}' was not found.")
            return pd.DataFrame()
        return pd.read_csv(file_path)

    def _load_claims(self, file_path: str) -> None:
        self.claims = self._safe_read_csv(file_path)

    def _load_evidence_reqs(self, file_path: str) -> None:
        self.evidence_reqs = self._safe_read_csv(file_path)

    def _load_output(self, file_path: str) -> None:
        self.output = self._safe_read_csv(file_path)

    def _load_user_history(self, file_path: str) -> None:
        self.user_history = self._safe_read_csv(file_path)

    def describe(self) -> None:
        """Provides an clean, scannable data visualization profile overview without console spam."""
        if self.claims.empty:
            print("\n--- 📚 Data Profile: Claims DataFrame is empty ---")
            return

        print('\n--- 📚 Describing Claims Data 📚 ---')
        print(f'Shape Matrix Dimensions: {self.claims.shape}')
        print(f'Columns Extracted: {list(self.claims.columns)}')

        # Fixed: Targeted value distribution tracking
        if 'claim_object' in self.claims.columns:
            print(f'\nObject Distribution:\n{self.claims["claim_object"].value_counts().head(5)}')

        print('\n--- Dataframe Summary Profiles ---')
        print(self.claims.describe().T)
        print(f'\nLabel Missing `NULL` Value Counters:\n{self.claims.isnull().sum()}')