# ADR 0006: Data Import UI Implementation

## Status

Accepted

## Context

The application needs a user-friendly interface for importing running data from CSV files. The interface should support:

1. Browsing and selecting CSV files
2. Choosing the appropriate format (standard, raw workout, or Stryd)
3. Previewing the data before import
4. Handling errors gracefully

## Decision

We implemented a TUI-based data import screen with the following features:

1. File Browser:

   - Directory navigation
   - CSV file filtering
   - Sorted by modification time
   - Scrollable list for many files

2. Format Selection:

   - Cycling through available formats
   - Format-specific parsing
   - Format indicator in UI

3. Data Preview:

   - Quick view of first 3 sessions
   - Basic metrics display
   - Error feedback

4. Implementation Details:
   - Used blessed for TUI components
   - Implemented responsive layout
   - Added keyboard navigation
   - Proper error handling and status messages

## Consequences

### Positive

1. Intuitive file selection interface
2. Easy format switching
3. Immediate data preview
4. Clear error feedback
5. Good test coverage

### Negative

1. Limited to terminal capabilities
2. No drag-and-drop support
3. Preview limited by terminal space

## Notes

- Consider adding file type detection
- May need pagination for large previews
- Could add search/filter functionality
