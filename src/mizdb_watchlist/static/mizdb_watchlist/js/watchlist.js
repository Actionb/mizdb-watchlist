(() => {
  async function act (btn) {
    const form = new FormData()
    form.append('object_id', btn.dataset.objectId)
    form.append('model_label', btn.dataset.modelLabel)
    return fetch(btn.dataset.url, {
      method: 'POST',
      headers: {
        'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
      },
      body: form,
      mode: 'same-origin'
    })
  }

  document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.watchlist-toggle-btn').forEach((btn) => {
      btn.addEventListener('click', (e) => {
        act(btn).then(response => response.json()).then(data => {
          if (data.on_watchlist) {
            btn.classList.remove('text-primary')
            btn.classList.add('text-success')
            btn.classList.add('on-watchlist')
          } else {
            btn.classList.add('text-primary')
            btn.classList.remove('text-success')
            btn.classList.remove('on-watchlist')
          }
        })
      })
    })
    document.querySelectorAll('.watchlist-remove-btn').forEach((btn) => {
      btn.addEventListener('click', (e) => {
        act(btn).then(response => {
          if (response.ok) {
            const li = btn.parentElement
            const ul = li.parentElement
            const div = ul.parentElement
            li.remove()
            if (ul.children.length === 0) div.remove()
          }
        })
      })
    })
  })
})()
