# ADR 0007: TUI Scrolling Behavior

## Status

Accepted

## Context

When implementing scrolling behavior in the TUI components, particularly in the session preview screen, we needed to decide how to handle scrolling when content fits within the visible area. The key considerations were:

1. User experience and expectations
2. Consistency with terminal-based applications
3. Prevention of unnecessary scrolling
4. Test behavior and validation

## Decision

We decided to implement a content-aware scrolling behavior with the following rules:

1. Scrolling is only enabled when content exceeds the visible area
2. The scroll offset is capped at the maximum possible scroll value (content length - visible height)
3. Scrolling up at the top or down at the bottom has no effect
4. The scroll offset is reset when switching views or sessions

This behavior is implemented in the `SessionPreviewScreen` class, where we:

- Calculate the maximum scroll value based on content length and visible height
- Only allow scrolling when there is content beyond the visible area
- Use `max` and `min` functions to ensure scroll offset stays within bounds

## Consequences

### Positive

1. More intuitive user experience by preventing unnecessary scrolling
2. Clearer behavior boundaries and edge cases
3. Easier to maintain and test with well-defined rules
4. Consistent with common terminal application behaviors

### Negative

1. Required modification of test expectations to match the intended behavior
2. Slightly more complex implementation to handle content-aware scrolling
3. Need to maintain padding logic to ensure proper scrolling in test environments

## Updates

- 2024-03-19: Initial implementation and acceptance
