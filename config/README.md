# Configuration Files

This directory contains JSON configuration files that control various aspects of the Qurban Management System.

## Files

### `vendors.json`
Contains vendor lists for different animal types:
- `sheep_vendors`: List of domba/kambing vendors
- `cow_vendors`: List of sapi vendors

### `animals.json`
Contains animal type definitions and categories:
- `animal_types`: Available animal types
- `sheep_categories`: Categories for domba/kambing with weights
- `cow_categories`: Categories for sapi with weights

### `sheets.json`
Contains sheet and date configurations:
- `sheet_names`: Google Sheets tab names for inbound/outbound
- `date_config`: Hari H dates for different forms

### `ui_labels.json`
Contains UI text and labels:
- `forms`: Form-specific labels and text
- `messages`: Success/error messages

## Usage

The configurations are loaded through the `ConfigHelper` class, which provides:
- Caching to avoid repeated file reads
- Type-safe access methods
- Convenience methods for common operations

## Modifying Configurations

1. **Adding vendors**: Edit `vendors.json` and add to the appropriate array
2. **Adding animal categories**: Edit `animals.json` 
3. **Changing sheet names**: Edit `sheets.json`
4. **Updating UI text**: Edit `ui_labels.json`

After making changes, restart the Streamlit application to see the updates. 