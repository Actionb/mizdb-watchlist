# Changelog

## [unreleased]

- enable overriding watchlist manager classes via settings

## 1.0.1 (2024-04-29)

- add missing `watchlist_init.js` to admin watchlist template

## 1.0.0 (2024-04-29)

- get CSRF value from cookie if not using token

- reworked toggle button:
    - toggling the toggle button now only toggles `on-watchlist` CSS class
      (was also toggling `text-primary` and `text-success`)
    - added `watchlist_toggle.css`
    - `toggle_button` template tag now accepts `classes` argument for providing own
      CSS classes
    - toggle button template no longer includes CSS classes
      `btn btn-link text-decoration-none` by default

- reworked how watchlist buttons are initialized:
    - `watchlist.js` no longer adds click event handlers when the page has been loaded
    - `watchlist.js` now exposes several init functions that must be called to
      add the click event handlers for their respective
      button: `initToggleButton`, `initRemoveButton`, `initRemoveAllButton`, `initButton`
    - the exposed functions allow users to add callback functions that will be called
      after the response from the server was handled
    - added `watchlist_init.js` that initializes all watchlist buttons on a page

## 0.1.8 (2024-04-10)

- tweak watchlist overview template and CSS
- toggle button template tag and watchlist link template tag now silence
  NoReverseMatch exceptions when URL name cannot be reversed

## 0.1.7 (2024-04-09)

- fix repository URL in pyproject.toml

## 0.1.6 (2024-04-09)

- initial release
