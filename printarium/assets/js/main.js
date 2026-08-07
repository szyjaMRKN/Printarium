/**
 * Printarium – skrypty motywu.
 * Bez zależności zewnętrznych (vanilla JS).
 */
(function () {
	'use strict';

	var i18n = (window.printariumData && window.printariumData.i18n) || {};

	/* ---------------------------------------------------------------
	 * Pomocnicze
	 * ------------------------------------------------------------ */
	function $(selector, scope) {
		return (scope || document).querySelector(selector);
	}

	function $$(selector, scope) {
		return Array.prototype.slice.call((scope || document).querySelectorAll(selector));
	}

	function on(element, event, handler) {
		if (element) {
			element.addEventListener(event, handler);
		}
	}

	/* ---------------------------------------------------------------
	 * Nagłówek – cień po przewinięciu
	 * ------------------------------------------------------------ */
	function initHeader() {
		var header = $('.site-header');
		if (!header) {
			return;
		}

		var update = function () {
			header.classList.toggle('is-scrolled', window.scrollY > 8);
		};

		update();
		window.addEventListener('scroll', update, { passive: true });
	}

	/* ---------------------------------------------------------------
	 * Panele wysuwane (menu mobilne, mini-koszyk, filtry)
	 * ------------------------------------------------------------ */
	var openPanel = null;
	var lastFocused = null;

	function backdrop() {
		var el = $('.pr-backdrop');
		if (!el) {
			el = document.createElement('div');
			el.className = 'pr-backdrop';
			document.body.appendChild(el);
			on(el, 'click', closePanel);
		}
		return el;
	}

	function openPanelEl(panel) {
		if (!panel) {
			return;
		}
		closePanel();
		lastFocused = document.activeElement;
		panel.classList.add('is-open');
		panel.removeAttribute('aria-hidden');
		backdrop().classList.add('is-open');
		document.body.classList.add('has-menu-open');
		openPanel = panel;

		var focusable = panel.querySelector('button, [href], input, select, textarea');
		if (focusable) {
			focusable.focus();
		}
	}

	function closePanel() {
		if (!openPanel) {
			return;
		}
		openPanel.classList.remove('is-open');
		openPanel.setAttribute('aria-hidden', 'true');
		backdrop().classList.remove('is-open');
		document.body.classList.remove('has-menu-open');
		openPanel = null;

		if (lastFocused) {
			lastFocused.focus();
			lastFocused = null;
		}
	}

	function initPanels() {
		on($('[data-printarium-menu-open]'), 'click', function (e) {
			e.preventDefault();
			openPanelEl($('#mobile-menu'));
		});

		$$('[data-printarium-menu-close]').forEach(function (btn) {
			on(btn, 'click', function (e) {
				e.preventDefault();
				closePanel();
			});
		});

		// Mini-koszyk – otwiera panel zamiast przechodzić na stronę koszyka.
		var miniCart = $('#mini-cart-panel');
		if (miniCart) {
			$$('[data-printarium-minicart-open]').forEach(function (link) {
				on(link, 'click', function (e) {
					e.preventDefault();
					openPanelEl(miniCart);
				});
			});
		}
		$$('[data-printarium-minicart-close]').forEach(function (btn) {
			on(btn, 'click', function (e) {
				e.preventDefault();
				closePanel();
			});
		});

		// Filtry sklepu na urządzeniach mobilnych.
		on($('[data-printarium-filters-open]'), 'click', function (e) {
			e.preventDefault();
			openPanelEl($('#shop-filters'));
		});
		on($('[data-printarium-filters-close]'), 'click', function (e) {
			e.preventDefault();
			closePanel();
		});

		document.addEventListener('keydown', function (e) {
			if (e.key === 'Escape') {
				closePanel();
				closeModals();
			}
		});
	}

	/* ---------------------------------------------------------------
	 * Wyszukiwarka w nagłówku
	 * ------------------------------------------------------------ */
	function initSearch() {
		var toggle = $('[data-printarium-search-toggle]');
		var panel = $('#header-search');

		if (!toggle || !panel) {
			return;
		}

		on(toggle, 'click', function (e) {
			e.preventDefault();
			var isOpen = panel.classList.toggle('is-open');
			toggle.setAttribute('aria-expanded', isOpen ? 'true' : 'false');

			if (isOpen) {
				var field = panel.querySelector('input[type="search"], input[type="text"]');
				if (field) {
					field.focus();
				}
			}
		});
	}

	/* ---------------------------------------------------------------
	 * Stepper ilości (+ / −)
	 * ------------------------------------------------------------ */
	function initSteppers() {
		document.addEventListener('click', function (e) {
			var btn = e.target.closest('.pr-stepper__btn');
			if (!btn) {
				return;
			}

			var wrap = btn.closest('.pr-stepper, .quantity');
			var input = wrap && wrap.querySelector('input[type="number"], input.qty');
			if (!input) {
				return;
			}

			var step = parseFloat(input.getAttribute('step')) || 1;
			var min = input.getAttribute('min') !== null ? parseFloat(input.getAttribute('min')) : 0;
			var maxAttr = input.getAttribute('max');
			var max = maxAttr !== null && maxAttr !== '' ? parseFloat(maxAttr) : Infinity;
			var value = parseFloat(input.value) || 0;

			value += btn.dataset.step === 'down' ? -step : step;
			value = Math.min(max, Math.max(min, value));

			input.value = value;
			input.dispatchEvent(new Event('change', { bubbles: true }));
		});
	}

	/**
	 * Dokłada przyciski +/− do pól ilości renderowanych przez WooCommerce.
	 */
	function decorateQuantityFields(scope) {
		$$('.quantity', scope || document).forEach(function (wrap) {
			if (wrap.dataset.prStepper === '1') {
				return;
			}

			var input = wrap.querySelector('input.qty');
			if (!input || input.type === 'hidden') {
				return;
			}

			wrap.dataset.prStepper = '1';

			var minus = document.createElement('button');
			minus.type = 'button';
			minus.className = 'pr-stepper__btn';
			minus.dataset.step = 'down';
			minus.setAttribute('aria-label', 'Zmniejsz ilość');
			minus.innerHTML = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" aria-hidden="true"><path d="M6 12h12"/></svg>';

			var plus = minus.cloneNode(false);
			plus.dataset.step = 'up';
			plus.setAttribute('aria-label', 'Zwiększ ilość');
			plus.innerHTML = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" aria-hidden="true"><path d="M12 6v12"/><path d="M6 12h12"/></svg>';

			wrap.insertBefore(minus, input);
			wrap.appendChild(plus);
		});
	}

	/* ---------------------------------------------------------------
	 * Akordeon / FAQ
	 * ------------------------------------------------------------ */
	function initAccordions() {
		$$('.pr-accordion').forEach(function (accordion) {
			var single = accordion.dataset.single === 'true';

			$$('.pr-accordion__trigger', accordion).forEach(function (trigger) {
				on(trigger, 'click', function () {
					var item = trigger.closest('.pr-accordion__item');
					var isOpen = item.classList.contains('is-open');

					if (single) {
						$$('.pr-accordion__item', accordion).forEach(function (other) {
							other.classList.remove('is-open');
							var t = other.querySelector('.pr-accordion__trigger');
							if (t) {
								t.setAttribute('aria-expanded', 'false');
							}
						});
					}

					item.classList.toggle('is-open', !isOpen);
					trigger.setAttribute('aria-expanded', !isOpen ? 'true' : 'false');
				});
			});
		});
	}

	/* ---------------------------------------------------------------
	 * Modale
	 * ------------------------------------------------------------ */
	function closeModals() {
		$$('.pr-modal.is-open').forEach(function (modal) {
			modal.classList.remove('is-open');
			modal.setAttribute('aria-hidden', 'true');
		});
		document.body.classList.remove('has-modal-open');
	}

	function initModals() {
		$$('[data-printarium-modal]').forEach(function (trigger) {
			on(trigger, 'click', function (e) {
				e.preventDefault();
				var modal = document.getElementById(trigger.dataset.printariumModal);
				if (!modal) {
					return;
				}
				modal.classList.add('is-open');
				modal.removeAttribute('aria-hidden');
				document.body.classList.add('has-modal-open');

				var focusable = modal.querySelector('input, textarea, button');
				if (focusable) {
					focusable.focus();
				}
			});
		});

		$$('.pr-modal').forEach(function (modal) {
			on(modal, 'click', function (e) {
				if (e.target === modal || e.target.closest('[data-printarium-modal-close]')) {
					closeModals();
				}
			});
		});
	}

	/* ---------------------------------------------------------------
	 * Toasty
	 * ------------------------------------------------------------ */
	var ICONS = {
		success: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="m8 12.4 2.6 2.6L16 9.6"/></svg>',
		error: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="m9 9 6 6"/><path d="m15 9-6 6"/></svg>',
		info: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M12 11v5"/><path d="M12 8h.01"/></svg>'
	};

	function toastContainer() {
		var el = $('.pr-toasts');
		if (!el) {
			el = document.createElement('div');
			el.className = 'pr-toasts';
			el.setAttribute('role', 'status');
			el.setAttribute('aria-live', 'polite');
			document.body.appendChild(el);
		}
		return el;
	}

	function toast(message, type) {
		type = type || 'success';

		var el = document.createElement('div');
		el.className = 'pr-toast pr-toast--' + type;
		el.innerHTML =
			'<span class="pr-toast__icon">' + (ICONS[type] || ICONS.info) + '</span>' +
			'<span class="pr-toast__text"></span>' +
			'<button type="button" class="pr-toast__close" aria-label="Zamknij">' +
			'<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" aria-hidden="true"><path d="m6 6 12 12"/><path d="m18 6-12 12"/></svg>' +
			'</button>';

		el.querySelector('.pr-toast__text').textContent = message;

		var remove = function () {
			el.classList.add('is-leaving');
			setTimeout(function () {
				el.remove();
			}, 200);
		};

		on(el.querySelector('.pr-toast__close'), 'click', remove);
		toastContainer().appendChild(el);
		setTimeout(remove, 4000);
	}

	window.printariumToast = toast;

	/* ---------------------------------------------------------------
	 * WooCommerce – reakcje na zdarzenia
	 * ------------------------------------------------------------ */
	function initWooEvents() {
		if (!window.jQuery) {
			return;
		}

		var $doc = window.jQuery(document.body);

		$doc.on('added_to_cart', function () {
			toast(i18n.added || 'Produkt dodany do koszyka', 'success');
		});

		$doc.on('wc_fragments_refreshed wc_fragments_loaded updated_wc_div updated_cart_totals', function () {
			decorateQuantityFields();
		});
	}

	/* ---------------------------------------------------------------
	 * Przełącznik widoku siatka / lista
	 * ------------------------------------------------------------ */
	function initViewToggle() {
		var main = $('.shop-main');
		var buttons = $$('[data-printarium-view]');

		if (!main || !buttons.length) {
			return;
		}

		var apply = function (view) {
			main.classList.toggle('is-list-view', view === 'list');
			buttons.forEach(function (btn) {
				var active = btn.dataset.printariumView === view;
				btn.classList.toggle('is-active', active);
				btn.setAttribute('aria-pressed', active ? 'true' : 'false');
			});
			try {
				window.localStorage.setItem('printariumView', view);
			} catch (err) {
				/* pamięć niedostępna – pomijamy */
			}
		};

		buttons.forEach(function (btn) {
			on(btn, 'click', function () {
				apply(btn.dataset.printariumView);
			});
		});

		try {
			var saved = window.localStorage.getItem('printariumView');
			if (saved) {
				apply(saved);
			}
		} catch (err) {
			/* pamięć niedostępna – pomijamy */
		}
	}

	/* ---------------------------------------------------------------
	 * Ulubione (lokalnie, w przeglądarce)
	 * ------------------------------------------------------------ */
	function initWishlist() {
		var storeKey = 'printariumWishlist';

		var read = function () {
			try {
				return JSON.parse(window.localStorage.getItem(storeKey) || '[]');
			} catch (err) {
				return [];
			}
		};

		var write = function (list) {
			try {
				window.localStorage.setItem(storeKey, JSON.stringify(list));
			} catch (err) {
				/* pamięć niedostępna – pomijamy */
			}
		};

		var saved = read();

		$$('[data-printarium-wishlist]').forEach(function (btn) {
			var id = btn.dataset.printariumWishlist;

			if (saved.indexOf(id) !== -1) {
				btn.setAttribute('aria-pressed', 'true');
			}

			on(btn, 'click', function () {
				var list = read();
				var index = list.indexOf(id);

				if (index === -1) {
					list.push(id);
					btn.setAttribute('aria-pressed', 'true');
				} else {
					list.splice(index, 1);
					btn.setAttribute('aria-pressed', 'false');
				}

				write(list);
			});
		});
	}

	/* ---------------------------------------------------------------
	 * Podmenu mobilne – rozwijanie
	 * ------------------------------------------------------------ */
	function initMobileSubmenus() {
		$$('.mobile-menu__list .menu-item-has-children > a').forEach(function (link) {
			var submenu = link.parentNode.querySelector('.sub-menu');
			if (!submenu) {
				return;
			}

			var toggle = document.createElement('button');
			toggle.type = 'button';
			toggle.className = 'btn-icon btn-icon--bare btn-icon--sm';
			toggle.setAttribute('aria-expanded', 'false');
			toggle.setAttribute('aria-label', 'Rozwiń podmenu');
			toggle.innerHTML = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m6 9.5 6 6 6-6"/></svg>';

			submenu.style.display = 'none';
			link.parentNode.insertBefore(toggle, submenu);
			link.style.flex = '1';

			on(toggle, 'click', function () {
				var isOpen = submenu.style.display !== 'none';
				submenu.style.display = isOpen ? 'none' : 'block';
				toggle.setAttribute('aria-expanded', isOpen ? 'false' : 'true');
				toggle.style.transform = isOpen ? '' : 'rotate(180deg)';
			});
		});
	}

	/* ---------------------------------------------------------------
	 * Strefa upuszczania plików w modalu „Projekt na zamówienie”
	 * ------------------------------------------------------------ */
	function initDropzones() {
		$$('.pr-dropzone').forEach(function (zone) {
			var input = zone.querySelector('input[type="file"]');
			var title = zone.querySelector('.pr-dropzone__title');

			if (!input) {
				return;
			}

			on(zone, 'click', function () {
				input.click();
			});

			['dragenter', 'dragover'].forEach(function (evt) {
				on(zone, evt, function (e) {
					e.preventDefault();
					zone.classList.add('is-dragover');
				});
			});

			['dragleave', 'drop'].forEach(function (evt) {
				on(zone, evt, function (e) {
					e.preventDefault();
					zone.classList.remove('is-dragover');
				});
			});

			on(zone, 'drop', function (e) {
				if (e.dataTransfer && e.dataTransfer.files.length) {
					input.files = e.dataTransfer.files;
					input.dispatchEvent(new Event('change', { bubbles: true }));
				}
			});

			on(input, 'change', function () {
				if (input.files.length && title) {
					title.textContent = input.files.length === 1 ? input.files[0].name : input.files.length + ' plików';
				}
			});
		});
	}

	/* ---------------------------------------------------------------
	 * Start
	 * ------------------------------------------------------------ */
	function init() {
		initHeader();
		initPanels();
		initSearch();
		initSteppers();
		decorateQuantityFields();
		initAccordions();
		initModals();
		initViewToggle();
		initWishlist();
		initMobileSubmenus();
		initDropzones();
		initWooEvents();
	}

	if (document.readyState === 'loading') {
		document.addEventListener('DOMContentLoaded', init);
	} else {
		init();
	}
})();
