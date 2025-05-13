import math
import re
import logging
from dataclasses import dataclass, field
from typing import List, Dict, Any, Callable, Optional

import pandas as pd

# Placeholder for CPLot, CPWafer, CPParameter from python_cp.数据类型定义
# These should be imported from the actual data_models module in a real scenario
# For example: from ..data_models.cp_data_model import CPLot, CPWafer, CPParameter
# Or from a sibling file: from .数据类型定义 import CPLot, CPWafer, CPParameter
# For this standalone script, we define minimal placeholders or use Any.

@dataclass
class CPParameter:
    id: str = \"\"
    name: str = \"\"
    unit: Optional[str] = None
    sl: Optional[float] = None
    su: Optional[float] = None
    test_conditions: List[str] = field(default_factory=list)
    # Add other fields as necessary, like display_name, etc.
    display_name: str = \"\" 

@dataclass
class CPWafer:
    wafer_id: str
    chip_data: Optional[pd.DataFrame] = None # Rows: chips, Columns: parameter_ids
    param_count: int = 0
    chip_count: int = 0
    # Add other fields as necessary

@dataclass
class CPLot:
    lot_id: str
    params: List[CPParameter] = field(default_factory=list)
    wafers: List[CPWafer] = field(default_factory=list)
    param_count: int = 0
    wafer_count: int = 0
    # Add other fields as necessary


logger = logging.getLogger(__name__)

@dataclass
class CalculatedParameterSetup:
    new_param_name: str
    new_param_id: str
    original_formula: str  # The "fN" style formula
    python_formula: str    # Formula transformed for Python's eval()
    dependent_param_ids: List[str] # Actual IDs from CPLot.params this formula depends on
    unit: Optional[str] = None
    sl: Optional[float] = None
    su: Optional[float] = None

@dataclass
class CalculatedParameterConfig:
    setups: List[CalculatedParameterSetup] = field(default_factory=list)

# Allowed functions and constants for eval context
EVAL_GLOBALS: Dict[str, Any] = {
    # Math functions
    "abs": abs,
    "sqrt": math.sqrt,
    "log": math.log,
    "log10": math.log10,
    "exp": math.exp,
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "asin": math.asin,
    "acos": math.acos,
    "atan": math.atan,
    "degrees": math.degrees,
    "radians": math.radians,
    # Math constants
    "pi": math.pi,
    "e": math.e,
    # Built-in functions
    "max": max,
    "min": min,
    "round": round,
    "pow": pow, # Alias for ** operator if preferred
}

def _transform_formula(fn_formula: str, existing_param_ids: List[str]) -> tuple[str, List[str]]:
    """
    Transforms an "fN" style formula string into a Python-evaluable string
    and identifies dependent parameter IDs.
    Example: "f1 + Abs(f2-f3)*100" with existing_param_ids ["ID_A", "ID_B", "ID_C"]
    becomes "ID_A + abs(ID_B-ID_C)*100" and dependent_ids ["ID_A", "ID_B", "ID_C"]
    """
    
    processed_formula = fn_formula
    dependent_ids_found = set()

    # Replace fN with actual parameter IDs
    def replace_fn(match):
        param_index = int(match.group(1)) - 1 # fN is 1-indexed
        if 0 <= param_index < len(existing_param_ids):
            param_id = existing_param_ids[param_index]
            dependent_ids_found.add(param_id)
            return str(param_id) # Ensure it's a string, might need quoting if IDs aren't valid Python identifiers
        else:
            raise ValueError(f"Formula variable {match.group(0)} out of bounds for existing parameters.")

    # Parameter IDs should be valid Python identifiers or handled carefully by eval.
    # Assuming param_ids are like 'VOLT_1', 'CURR_A' etc.
    # We need to ensure that when these IDs are substituted, they are treated as variables.
    # A simple way is to ensure they are valid Python var names.
    # If not, the locals_dict keys for eval must match exactly.
    processed_formula = re.sub(r"f(\d+)", replace_fn, processed_formula)

    # Normalize function names (e.g., Abs to abs)
    # This simple replacement might not be robust for all cases (e.g., substring issues)
    # A more robust way would be to parse known functions.
    for func_name_excel, func_py in EVAL_GLOBALS.items():
        if isinstance(func_py, Callable): # Only map function names
             # Case-insensitive replacement for known function names
            processed_formula = re.sub(r'\\b' + re.escape(func_name_excel) + r'\\b', func_name_excel, processed_formula, flags=re.IGNORECASE)
            # Correct common Excel function capitalization differences if any
            # For example, if Excel uses ABS and Python uses abs
            processed_formula = processed_formula.replace(func_name_excel.upper(), func_name_excel.lower())
            processed_formula = processed_formula.replace(func_name_excel.capitalize(), func_name_excel.lower())


    # Ensure Pythonic power operator if ^ is used
    processed_formula = processed_formula.replace('^', '**')

    return processed_formula, sorted(list(dependent_ids_found))


def read_calculation_setup(
    excel_path: str, 
    sheet_name: str, 
    existing_param_names_ordered: List[str]
) -> CalculatedParameterConfig:
    """
    Reads calculation setup from an Excel sheet.
    The Excel sheet should have columns:
    Row 1: New Parameter Name (e.g., "Resistance")
    Row 2: New Parameter ID (e.g., "R_calc")
    Row 3: Formula using "fN" notation (e.g., "f1/f2" where f1 is voltage, f2 is current)
    Row 4: Unit (e.g., "Ohm")
    Row 5: Lower Spec Limit (SL) (optional, e.g., 100.0)
    Row 6: Upper Spec Limit (SU) (optional, e.g., 200.0)

    Each column represents a new parameter to be calculated.
    `existing_param_names_ordered` is the list of IDs of parameters already present
    in the CPLot data, in the order corresponding to f1, f2, ...
    """
    try:
        df_setup = pd.read_excel(excel_path, sheet_name=sheet_name, header=None)
    except FileNotFoundError:
        logger.error(f"Excel setup file not found: {excel_path}")
        return CalculatedParameterConfig()
    except Exception as e:
        logger.error(f"Error reading Excel setup file {excel_path}, sheet {sheet_name}: {e}")
        return CalculatedParameterConfig()

    if df_setup.empty:
        logger.warning(f"No setup data found in {excel_path}, sheet {sheet_name}.")
        return CalculatedParameterConfig()

    setups = []
    # Iterate over columns, each column is a new parameter setup
    for col_idx in range(df_setup.shape[1]):
        try:
            col_data = df_setup.iloc[:, col_idx]
            if col_data.iloc[2] == "" or pd.isna(col_data.iloc[2]): # Formula is mandatory
                logger.debug(f"Skipping column {col_idx+1} in setup: No formula provided.")
                continue

            new_param_name = str(col_data.iloc[0])
            new_param_id = str(col_data.iloc[1])
            fn_formula = str(col_data.iloc[2])
            
            unit = str(col_data.iloc[3]) if pd.notna(col_data.iloc[3]) and col_data.iloc[3] != "" else None
            
            sl_val = col_data.iloc[4] if len(col_data) > 4 and pd.notna(col_data.iloc[4]) else None
            su_val = col_data.iloc[5] if len(col_data) > 5 and pd.notna(col_data.iloc[5]) else None

            sl = float(sl_val) if sl_val is not None else None
            su = float(su_val) if su_val is not None else None
            
            # Check for duplicate new_param_id
            if any(s.new_param_id == new_param_id for s in setups):
                logger.warning(f"Duplicate new parameter ID '{new_param_id}' in setup. Skipping subsequent definition.")
                continue
            if new_param_id in existing_param_names_ordered:
                logger.warning(f"New parameter ID '{new_param_id}' conflicts with an existing parameter ID. Skipping.")
                continue


            logger.info(f"Processing new parameter: ID='{new_param_id}', Name='{new_param_name}', Formula='{fn_formula}'")
            python_formula, dependent_ids = _transform_formula(fn_formula, existing_param_names_ordered)
            
            setup = CalculatedParameterSetup(
                new_param_name=new_param_name,
                new_param_id=new_param_id,
                original_formula=fn_formula,
                python_formula=python_formula,
                dependent_param_ids=dependent_ids,
                unit=unit,
                sl=sl,
                su=su
            )
            setups.append(setup)
        except IndexError:
            logger.warning(f"Column {col_idx+1} in Excel setup sheet '{sheet_name}' has insufficient rows (expected at least 3). Skipping.")
        except ValueError as ve:
            logger.error(f"Error processing formula for column {col_idx+1} ('{col_data.iloc[0]}'): {ve}. Skipping.")
        except Exception as e:
            logger.error(f"Unexpected error processing column {col_idx+1} ('{col_data.iloc[0]}') in setup: {e}. Skipping.")
            
    return CalculatedParameterConfig(setups=setups)


def add_calculated_parameters(
    cp_lot_data: CPLot, 
    config: CalculatedParameterConfig
) -> CPLot:
    """
    Adds new parameters to CPLot data based on the provided calculation configuration.
    Modifies cp_lot_data in-place and also returns it.
    """
    if not config.setups:
        logger.info("No calculated parameter setups to process.")
        return cp_lot_data

    existing_param_ids_in_plot = [p.id for p in cp_lot_data.params]

    # 1. Add new parameter definitions to CPLot.params
    for setup in config.setups:
        if setup.new_param_id in existing_param_ids_in_plot:
            logger.warning(f"Calculated parameter ID '{setup.new_param_id}' already exists in CPLot.params. It might be overwritten if names match, or cause issues if data types differ.")
            # Optionally, remove or update existing before adding new
        
        # Ensure all dependent parameters actually exist in the chip_data columns
        # This check is more about the chip_data integrity, assuming CPLot.params is source of truth for IDs
        
        cp_lot_data.params.append(CPParameter(
            id=setup.new_param_id,
            name=setup.new_param_name, # Or use a more specific 'display_name'
            display_name=setup.new_param_name,
            unit=setup.unit,
            sl=setup.sl,
            su=setup.su,
            test_conditions=[f"Calculated: {setup.original_formula}"] # Store original formula
        ))
        existing_param_ids_in_plot.append(setup.new_param_id) # Keep track for subsequent additions

    cp_lot_data.param_count = len(cp_lot_data.params)

    # 2. Iterate through wafers and their chip_data
    for wafer in cp_lot_data.wafers:
        if wafer.chip_data is None or wafer.chip_data.empty:
            logger.warning(f"Wafer {wafer.wafer_id} has no chip data to process for calculations.")
            continue

        current_wafer_chip_data_cols = wafer.chip_data.columns.tolist()

        # Add new columns to chip_data DataFrame for each wafer, initialized with NaN
        for setup in config.setups:
            if setup.new_param_id not in current_wafer_chip_data_cols:
                wafer.chip_data[setup.new_param_id] = pd.NA # Use pd.NA for pandas >= 1.0 or np.nan

        # 3. Perform calculations for each chip
        for setup in config.setups:
            # Check if all dependent parameters for this formula exist in the current wafer's chip_data
            missing_deps = [dep_id for dep_id in setup.dependent_param_ids if dep_id not in current_wafer_chip_data_cols]
            if missing_deps:
                logger.error(f"Wafer {wafer.wafer_id}: Missing dependent parameters {missing_deps} for formula '{setup.original_formula}' (new_param: {setup.new_param_id}). Skipping calculation for this parameter on this wafer.")
                wafer.chip_data[setup.new_param_id] = pd.NA # Ensure column is NaN
                continue
            
            # Apply calculation row-wise
            def calculate_row(row):
                locals_dict = {dep_id: row[dep_id] for dep_id in setup.dependent_param_ids}
                
                # Check for any NaN in dependent values; if so, result is NaN
                if any(pd.isna(val) for val in locals_dict.values()):
                    return pd.NA

                try:
                    return eval(setup.python_formula, EVAL_GLOBALS, locals_dict)
                except ZeroDivisionError:
                    logger.debug(f"ZeroDivisionError for {setup.new_param_id} on wafer {wafer.wafer_id}, formula: '{setup.python_formula}', row data: {row.to_dict()}")
                    return pd.NA
                except TypeError as te:
                    logger.debug(f"TypeError for {setup.new_param_id} (e.g. math func on non-numeric) on wafer {wafer.wafer_id}, formula: '{setup.python_formula}', locals: {locals_dict}, error: {te}")
                    return pd.NA
                except Exception as e:
                    logger.warning(f"Error evaluating formula for {setup.new_param_id} on wafer {wafer.wafer_id}: {e}. Formula: '{setup.python_formula}'. Row data relevant: {locals_dict}")
                    return pd.NA
            
            if not setup.dependent_param_ids and "f" in setup.original_formula.lower():
                 logger.warning(f"Formula '{setup.original_formula}' for '{setup.new_param_id}' seems to use 'fN' variables but no dependent IDs were extracted. This might be an error in _transform_formula or the formula itself. Calculation will likely fail or produce NaN.")
                 wafer.chip_data[setup.new_param_id] = pd.NA
            elif not wafer.chip_data.empty: # Only apply if there's data
                wafer.chip_data[setup.new_param_id] = wafer.chip_data.apply(calculate_row, axis=1)
            else: # chip_data is empty, but columns were added
                 pass # Columns are already NaN

        wafer.param_count = len(wafer.chip_data.columns) if wafer.chip_data is not None else 0


    logger.info("Finished processing calculated parameters.")
    return cp_lot_data

if __name__ == '__main__':
    # Basic logging setup for testing
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    # --- Create Mock CPLot Data ---
    # Parameters that already exist in the data
    param_v = CPParameter(id="VOLT", name="Voltage", unit="V")
    param_i = CPParameter(id="CURR", name="Current", unit="A")
    param_t = CPParameter(id="TEMP", name="Temperature", unit="C")
    
    existing_params_list = [param_v, param_i, param_t]
    existing_param_ids_ordered = [p.id for p in existing_params_list] # Order matters for "fN"

    # Wafer 1 Data
    chip_data_w1 = pd.DataFrame({
        "VOLT": [1.0, 1.1, 0.9, 1.0, pd.NA], # One NA value
        "CURR": [0.1, 0.11, 0.09, 0.0, 0.1], # One zero value for division test
        "TEMP": [25.0, 25.1, 24.9, 25.0, 25.0]
    })
    wafer1 = CPWafer(wafer_id="W01", chip_data=chip_data_w1, param_count=len(existing_param_ids_ordered), chip_count=len(chip_data_w1))

    # Wafer 2 Data (empty chip data to test handling)
    wafer2 = CPWafer(wafer_id="W02", chip_data=pd.DataFrame(columns=existing_param_ids_ordered), param_count=len(existing_param_ids_ordered), chip_count=0)
    
    # Wafer 3 Data (all good)
    chip_data_w3 = pd.DataFrame({
        "VOLT": [5.0, 5.1],
        "CURR": [2.0, 2.1],
        "TEMP": [30.0, 30.5]
    })
    wafer3 = CPWafer(wafer_id="W03", chip_data=chip_data_w3, param_count=len(existing_param_ids_ordered), chip_count=len(chip_data_w3))


    cp_lot = CPLot(
        lot_id="TestLot123",
        params=existing_params_list,
        wafers=[wafer1, wafer2, wafer3],
        param_count=len(existing_params_list),
        wafer_count=3
    )

    # --- Create Mock Excel Setup File ---
    # In a real scenario, this would be an Excel file.
    # For testing, we simulate its content with a DataFrame.
    excel_setup_data = {
        0: ["Resistance", "R_OHM", "f1/f2", "Ohm", 10.0, 100.0], # VOLT/CURR
        1: ["Power", "P_WATT", "f1*f2", "Watt", 0.01, 10.0],    # VOLT*CURR
        2: ["Temp_K", "T_KELVIN", "f3+273.15", "K", 273.15, 373.15], # TEMP + 273.15
        3: ["V_Squared", "V_SQ", "f1**2", "V^2", None, None], # VOLT squared
        4: ["Log_V", "LOG_VOLT", "log(f1)", None, None, None], # Log of VOLT
        5: ["Invalid_Formula", "INV_F", "f1/f99", "ErrorUnit", None, None], # f99 is out of bounds
        6: ["V_plus_const", "V_CONST", "f1 + pi", "V", None, None], # VOLT + pi
        7: ["Max_V_I", "MAX_VI", "max(f1, f2)", "Units", None, None] # Max of VOLT and CURR
    }
    df_mock_excel = pd.DataFrame(excel_setup_data)
    mock_excel_file_path = "mock_calc_setup.xlsx"
    df_mock_excel.to_excel(mock_excel_file_path, sheet_name="Sheet1", header=False, index=False)
    logger.info(f"Mock Excel setup file created at {mock_excel_file_path}")

    # --- Test read_calculation_setup ---
    logger.info("\\n--- Testing read_calculation_setup ---")
    calculation_config = read_calculation_setup(mock_excel_file_path, "Sheet1", existing_param_ids_ordered)
    if calculation_config.setups:
        for i, setup_item in enumerate(calculation_config.setups):
            logger.info(f"Read setup item {i+1}:")
            logger.info(f"  Name: {setup_item.new_param_name}, ID: {setup_item.new_param_id}")
            logger.info(f"  Original Formula: '{setup_item.original_formula}'")
            logger.info(f"  Python Formula: '{setup_item.python_formula}'")
            logger.info(f"  Dependent IDs: {setup_item.dependent_param_ids}")
            logger.info(f"  Unit: {setup_item.unit}, SL: {setup_item.sl}, SU: {setup_item.su}")
    else:
        logger.warning("No calculation setups were read.")
        

    # --- Test add_calculated_parameters ---
    logger.info("\\n--- Testing add_calculated_parameters ---")
    if calculation_config.setups: # Only proceed if setups were read
      cp_lot_updated = add_calculated_parameters(cp_lot, calculation_config)

      logger.info(f"Updated CPLot.params (Count: {cp_lot_updated.param_count}):")
      for p in cp_lot_updated.params:
          logger.info(f"  ID: {p.id}, Name: {p.name}, Unit: {p.unit}, SL: {p.sl}, SU: {p.su}, Conditions: {p.test_conditions}")

      for w_idx, wafer_updated in enumerate(cp_lot_updated.wafers):
          logger.info(f"\\nWafer {wafer_updated.wafer_id} (Original index {w_idx}) - Chip Data (Param Count: {wafer_updated.param_count}):")
          if wafer_updated.chip_data is not None:
              # For cleaner display, convert pd.NA to string 'NaN' or similar
              print(wafer_updated.chip_data.to_string())
          else:
              logger.info("  No chip data.")
    else:
        logger.info("Skipping add_calculated_parameters test as no setups were loaded.")

    # Clean up mock file
    import os
    try:
        os.remove(mock_excel_file_path)
        logger.info(f"Mock Excel file {mock_excel_file_path} removed.")
    except OSError as e:
        logger.error(f"Error removing mock Excel file: {e}") 