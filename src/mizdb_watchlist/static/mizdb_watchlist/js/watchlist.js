/**
 * mizdb_watchlist
 *
 * Click event handlers for the various watchlist buttons.
 */

const WatchlistButton = (() => {
  /**
   * Return the CSRF token.
   *
   * @returns the CSRF token
   */
  function getCSRFToken () {
    const csrfInput = document.querySelector('[name=csrfmiddlewaretoken]')
    if (csrfInput) {
      return csrfInput.value
    } else {
      // Get token from cookie:
      // https://docs.djangoproject.com/en/5.0/howto/csrf/#acquiring-the-token-if-csrf-use-sessions-and-csrf-cookie-httponly-are-false
      if (document.cookie && document.cookie !== '') {
        const name = 'csrftoken'
        const cookies = document.cookie.split(';')
        for (let i = 0; i < cookies.length; i++) {
          const cookie = cookies[i].trim()
          // Does this cookie string begin with the name we want?
          if (cookie.substring(0, name.length + 1) === (name + '=')) {
            return decodeURIComponent(cookie.substring(name.length + 1))
          }
        }
      }
    }
    throw new Error('No CSRF Token set.')
  }

  /**
   * Create a POST request that notifies the server about changes to the watchlist
   * for the button's model object.
   *
   * The URL provided by the button's dataset determines the type of change
   * (i.e. either 'toggle' or 'remove').
   *
   * The model object is described by the attributes set in the button's dataset.
   *
   * @param {HTMLButtonElement} btn the watchlist button
   * @returns a new Request instance
   */
  function getRequest (btn) {
    const form = new FormData()
    form.append('object_id', btn.dataset.objectId)
    form.append('model_label', btn.dataset.modelLabel)
    return new Request(btn.dataset.url, {
      method: 'POST',
      headers: {
        'X-CSRFToken': getCSRFToken()
      },
      body: form,
      mode: 'same-origin'
    })
  }

  /**
   * For the given button, return the parent container that contains the
   * watchlist items of a single model.
   *
   * @param {HTMLButtonElement} btn the watchlist button
   * @returns the button's parent model-watchlist-container
   */
  function getModelContainer (btn) {
    return btn.closest('.model-watchlist-container')
  }

  /**
   * Remove all watchlist items in the parent model container of the clicked
   * button.
   *
   * @param {HTMLButtonElement} btn the 'remove' button that was clicked
   */
  function removeModel (btn) {
    getModelContainer(btn).remove()
    if (!document.querySelector('.model-watchlist-container')) {
      const emptyMessage = document.getElementById('empty-watchlist')
      if (emptyMessage) emptyMessage.style = 'display: block;'
    }
  }

  /**
   * Initialize a watchlist button, adding a click event handler.
   *
   * The event handler will make a request against the URL declared in
   * the button's dataset property. The second argument ``handleResponse``
   * will be called with the clicked button and the response to act on the
   * response.
   *
   * Then, if provided, the third argument ``callback`` will be called with
   * the button and the data returned by ``handleResponse``.
   *
   * @param {HTMLButtonElement} btn the button to initialize
   * @param {CallableFunction} handleResponse a function that handles the response
   * @param {CallableFunction} callback an optional function called at the end of the click event handling
   */
  function initButton (btn, handleResponse, callback) {
    if (btn.initialized) {
      console.log(`${btn} already initialized.`)
      return
    }
    btn.addEventListener('click', (event) => {
      event.preventDefault()
      fetch(getRequest(btn))
        .then(response => handleResponse(btn, response))
        .then(data => { if (callback) { callback(btn, data) } })
        .catch((error) => console.log(`watchlist button ${btn} error: ${error}`))
    })
    btn.initialized = true
  }

  /**
   * Initialize a 'toggle' button that adds an item to the watchlist, or
   * removes an item from the watchlist if it is already on the watchlist.
   */
  function initToggleButton (btn, callback) {
    const _callback = (btn, data) => {
      // always toggle the 'on-watchlist' class
      if (data) {
        if (data.on_watchlist) {
          btn.classList.add('on-watchlist')
        } else {
          btn.classList.remove('on-watchlist')
        }
      }
      if (callback) callback(btn, data)
    }
    const handleResponse = (btn, response) => {
      if (!response.ok) {
        throw new Error(`Toggle response was not ok (status code: ${response.status})`)
      }
      return response.json()
    }
    initButton(btn, handleResponse, _callback)
  }

  /**
   * Initialize a 'remove' button that removes a single item from the
   * watchlist. Used on the watchlist overview.
   */
  function initRemoveButton (btn, callback) {
    const handleResponse = (btn, response) => {
      if (response.ok) {
        if (btn.closest('.watchlist-items-list').children.length === 1) {
          // This is the only watchlist item for that model - remove the
          // model container.
          removeModel(btn)
        } else {
          // Remove just this watchlist item.
          btn.closest('.watchlist-item').remove()
        }
      }
      return response.json()
    }
    initButton(btn, handleResponse, callback)
  }

  /**
   * Initialize a 'remove all' button that removes all items of a model from
   * the watchlist. Used on the watchlist overview.
   */
  function initRemoveAllButton (btn, callback) {
    const handleResponse = (btn, response) => {
      if (response.ok) removeModel(btn)
      return response.json()
    }
    initButton(btn, handleResponse, callback)
  }

  return {
    initToggleButton,
    initRemoveButton,
    initRemoveAllButton,
    initButton
  }
})()

window.WatchlistButton = WatchlistButton
