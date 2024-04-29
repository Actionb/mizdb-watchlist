/**
 * mizdb_watchlist
 *
 * Initialize any watchlist buttons in this document.
 */

document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.watchlist-toggle-btn').forEach((btn) => window.WatchlistButton.initToggleButton(btn))
  document.querySelectorAll('.watchlist-remove-btn').forEach((btn) => window.WatchlistButton.initRemoveButton(btn))
  document.querySelectorAll('.watchlist-remove-all-btn').forEach((btn) => window.WatchlistButton.initRemoveAllButton(btn))
})
