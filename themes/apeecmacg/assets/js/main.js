/* Search is progressive enhancement; navigation and content work without JavaScript. */
(() => {
  const results = document.querySelector('#search-results');
  if (!results) return;
  const input = document.querySelector('#query');
  const query = new URLSearchParams(window.location.search).get('q') || '';
  input.value = query;
  if (!query.trim()) return;
  const normalize = value => value.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLocaleLowerCase('pt');
  const words = normalize(query).trim().split(/\s+/);
  const message = text => {
    const p = document.createElement('p');
    p.textContent = text;
    results.replaceChildren(p);
  };
  message('A pesquisar…');
  fetch(results.dataset.index)
    .then(response => {
      if (!response.ok) throw new Error('Search index unavailable');
      return response.json();
    })
    .then(pages => {
      const matches = pages.filter(page => words.every(word => normalize(`${page.title} ${page.content}`).includes(word)));
      message(matches.length ? `${matches.length} resultado${matches.length === 1 ? '' : 's'} para “${query}”` : `Não foram encontrados resultados para “${query}”.`);
      const list = document.createElement('ul');
      list.className = 'search-results';
      matches.forEach(page => {
        const item = document.createElement('li');
        const link = document.createElement('a');
        link.href = page.url;
        link.textContent = page.title;
        const excerpt = document.createElement('p');
        excerpt.textContent = page.content.replace(/\s+/g, ' ').slice(0, 220) + '…';
        item.append(link, excerpt);
        list.append(item);
      });
      results.append(list);
    })
    .catch(() => message('Não foi possível carregar a pesquisa. Tente novamente ou consulte as novidades no menu.'));
})();
