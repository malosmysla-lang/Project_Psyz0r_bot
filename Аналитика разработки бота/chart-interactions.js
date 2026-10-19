/* Графики появляются при прокрутке. Числа и размеры столбцов не изменяются. */
(() => {
  if (!document.body || !window.MutationObserver) return;
  const reduced = matchMedia('(prefers-reduced-motion: reduce)');
  const seen = new WeakSet();
  const observer = window.IntersectionObserver ? new IntersectionObserver(entries => {
    entries.forEach(entry => {
      if (entry.isIntersecting) { entry.target.classList.add('chart-visible'); observer.unobserve(entry.target); }
    });
  }, {threshold: .15}) : null;
  const names = {Gauntlet:0, MG:1, SG:2, GL:3, Rocket:4, RL:4, LG:5, Rail:6, RG:6, Plasma:7, PG:7};
  function scan() {
    document.querySelectorAll('.bar i,.comparison-bar i,.histogram-bin i').forEach(fill => {
      if (seen.has(fill)) return;
      seen.add(fill); fill.classList.add('chart-fill');
      if (reduced.matches || !observer) fill.classList.add('chart-visible'); else observer.observe(fill);
    });
    document.querySelectorAll('.barrow,.comparison-bar,.histogram-bin').forEach(row => {
      if (row.dataset.chartTip) return;
      const text = row.getAttribute('title') || row.textContent.trim();
      row.dataset.chartTip = text; row.tabIndex = 0;
      row.addEventListener('click', () => row.classList.toggle('chart-touch'));
    });
    // Один атлас: восемь детальных боковых силуэтов без подмены показателей.
    document.querySelectorAll('.weapon-detail>strong,.cohort-comparison>strong,.histogram-panel h3,#cohortRows td:first-child').forEach(label => {
      if (label.querySelector('.weapon-icon')) return;
      const name = label.textContent.trim().split(/\s/)[0];
      const index = names[name]; if (index === undefined) return;
      const icon = document.createElement('span'); icon.className='weapon-icon'; icon.setAttribute('aria-hidden','true');
      icon.style.backgroundPosition=`${index%2*100}% ${Math.floor(index/2)*100/3}%`; label.prepend(icon);
    });
  }
  scan(); new MutationObserver(scan).observe(document.body,{childList:true,subtree:true});
})();
