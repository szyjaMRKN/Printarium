<?php
/**
 * Zestaw ikon SVG (zgodny z sekcją „7. IKONY” systemu projektowego).
 *
 * @package Printarium
 */

defined( 'ABSPATH' ) || exit;

/**
 * Zwraca kod SVG ikony.
 *
 * @param string $name Nazwa ikony.
 * @param int    $size Rozmiar w px (24 lub 32).
 * @param array  $args Dodatkowe atrybuty: class, label.
 * @return string
 */
function printarium_get_icon( $name, $size = 24, $args = array() ) {
	$paths = printarium_icon_paths();

	if ( ! isset( $paths[ $name ] ) ) {
		return '';
	}

	$class  = isset( $args['class'] ) ? ' ' . $args['class'] : '';
	$label  = isset( $args['label'] ) ? $args['label'] : '';
	$hidden = $label ? '' : ' aria-hidden="true" focusable="false"';
	$title  = $label ? '<title>' . esc_html( $label ) . '</title>' : '';
	$role   = $label ? ' role="img"' : '';

	return sprintf(
		'<svg class="pr-icon pr-icon--%1$s%2$s" width="%3$d" height="%3$d" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"%4$s%5$s>%6$s%7$s</svg>',
		esc_attr( $name ),
		esc_attr( $class ),
		(int) $size,
		$hidden,
		$role,
		$title,
		$paths[ $name ]
	);
}

/**
 * Wypisuje ikonę.
 *
 * @param string $name Nazwa ikony.
 * @param int    $size Rozmiar.
 * @param array  $args Argumenty.
 */
function printarium_icon( $name, $size = 24, $args = array() ) {
	echo printarium_get_icon( $name, $size, $args ); // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped
}

/**
 * Definicje ścieżek ikon.
 *
 * @return array
 */
function printarium_icon_paths() {
	return array(
		'search'      => '<circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/>',
		'user'        => '<circle cx="12" cy="8" r="3.5"/><path d="M4.5 20a7.5 7.5 0 0 1 15 0"/>',
		'cart'        => '<circle cx="9.5" cy="20" r="1.3"/><circle cx="17.5" cy="20" r="1.3"/><path d="M2.5 3h2.2l2.4 11.2a1.6 1.6 0 0 0 1.6 1.3h8.6a1.6 1.6 0 0 0 1.6-1.3L20.5 7H6"/>',
		'heart'       => '<path d="M12 20s-7.5-4.6-7.5-9.4A4.1 4.1 0 0 1 12 8a4.1 4.1 0 0 1 7.5 2.6C19.5 15.4 12 20 12 20Z"/>',
		'filter'      => '<path d="M3 7h11"/><path d="M18 7h3"/><path d="M3 12h4"/><path d="M11 12h10"/><path d="M3 17h9"/><path d="M16 17h5"/><circle cx="16" cy="7" r="2"/><circle cx="9" cy="12" r="2"/><circle cx="14" cy="17" r="2"/>',
		'menu'        => '<path d="M3.5 7h17"/><path d="M3.5 12h17"/><path d="M3.5 17h17"/>',
		'close'       => '<path d="m6 6 12 12"/><path d="m18 6-12 12"/>',
		'arrow-right' => '<path d="M4 12h15"/><path d="m13 6 6 6-6 6"/>',
		'arrow-left'  => '<path d="M20 12H5"/><path d="m11 6-6 6 6 6"/>',
		'plus'        => '<circle cx="12" cy="12" r="9"/><path d="M12 8v8"/><path d="M8 12h8"/>',
		'minus'       => '<circle cx="12" cy="12" r="9"/><path d="M8 12h8"/>',
		'plus-sm'     => '<path d="M12 6v12"/><path d="M6 12h12"/>',
		'minus-sm'    => '<path d="M6 12h12"/>',
		'check'       => '<circle cx="12" cy="12" r="9"/><path d="m8 12.4 2.6 2.6L16 9.6"/>',
		'check-bare'  => '<path d="m5 12.8 4.4 4.4L19 7.6"/>',
		'info'        => '<circle cx="12" cy="12" r="9"/><path d="M12 11v5"/><path d="M12 8h.01"/>',
		'warning'     => '<path d="M12 4.5 21 19.5H3L12 4.5Z"/><path d="M12 10v4"/><path d="M12 17h.01"/>',
		'error'       => '<circle cx="12" cy="12" r="9"/><path d="m9 9 6 6"/><path d="m15 9-6 6"/>',
		'trash'       => '<path d="M4.5 7h15"/><path d="M9.5 7V4.8h5V7"/><path d="M6.5 7v12.2a1.3 1.3 0 0 0 1.3 1.3h8.4a1.3 1.3 0 0 0 1.3-1.3V7"/><path d="M10.2 11v6"/><path d="M13.8 11v6"/>',
		'download'    => '<path d="M12 4v11"/><path d="m7.5 10.5 4.5 4.5 4.5-4.5"/><path d="M4.5 19.5h15"/>',
		'upload'      => '<path d="M6.5 17a3.5 3.5 0 0 1-.3-7 5.2 5.2 0 0 1 10-1.5A4 4 0 0 1 17.8 17"/><path d="M12 11v8"/><path d="m9 14 3-3 3 3"/>',
		'eye'         => '<path d="M2.5 12S6 5.5 12 5.5 21.5 12 21.5 12 18 18.5 12 18.5 2.5 12 2.5 12Z"/><circle cx="12" cy="12" r="3"/>',
		'refresh'     => '<path d="M20 12a8 8 0 1 1-2.6-5.9"/><path d="M20 4v4.5h-4.5"/>',
		'grid'        => '<rect x="4" y="4" width="6.5" height="6.5" rx="1.2"/><rect x="13.5" y="4" width="6.5" height="6.5" rx="1.2"/><rect x="4" y="13.5" width="6.5" height="6.5" rx="1.2"/><rect x="13.5" y="13.5" width="6.5" height="6.5" rx="1.2"/>',
		'list'        => '<path d="M4 6.5h16"/><path d="M4 12h16"/><path d="M4 17.5h16"/>',
		'chevron'     => '<path d="m6 9.5 6 6 6-6"/>',
		'phone'       => '<path d="M6.5 3.5h3l1.5 4-2 1.5a11 11 0 0 0 6 6l1.5-2 4 1.5v3a2 2 0 0 1-2.2 2A16.5 16.5 0 0 1 4.5 5.7a2 2 0 0 1 2-2.2Z"/>',
		'mail'        => '<rect x="3" y="5.5" width="18" height="13" rx="2"/><path d="m3.8 7 8.2 6 8.2-6"/>',
		'pin'         => '<path d="M12 21s6.5-6.1 6.5-10.5a6.5 6.5 0 0 0-13 0C5.5 14.9 12 21 12 21Z"/><circle cx="12" cy="10.5" r="2.5"/>',
		'box'         => '<path d="M12 2.8 20.5 7v10L12 21.2 3.5 17V7L12 2.8Z"/><path d="M3.5 7 12 11.5 20.5 7"/><path d="M12 11.5v9.7"/>',
		'pencil'      => '<path d="M4 20h4l10-10-4-4L4 16v4Z"/><path d="m14.5 5.5 4 4"/>',
		'shield'      => '<path d="M12 3 19.5 6v6c0 4.4-3.2 7.6-7.5 9-4.3-1.4-7.5-4.6-7.5-9V6L12 3Z"/>',
		'leaf'        => '<path d="M20 4S8 4 5.5 10.5C3.6 15.6 7 20 7 20s6.5-1 10-6.5"/><path d="M7 20c1-6 5-10 11-13"/>',
		'flask'       => '<path d="M9.5 3h5"/><path d="M10.5 3v6.2L5.6 17.8A2 2 0 0 0 7.3 21h9.4a2 2 0 0 0 1.7-3.2L13.5 9.2V3"/><path d="M8 15h8"/>',
		'paw'         => '<circle cx="7" cy="10" r="2"/><circle cx="12" cy="7.5" r="2"/><circle cx="17" cy="10" r="2"/><path d="M12 12c-3.2 0-5.5 2.4-5.5 4.7C6.5 19 8.5 20 12 20s5.5-1 5.5-3.3C17.5 14.4 15.2 12 12 12Z"/>',
		'poland'      => '<path d="M4 9.5 6.5 5l4 1 3-2.5 5 2.5-1 4 2 3-3 5-5 1-4-2-3-5 1-2.5Z"/>',
		'star'        => '<path d="m12 3.8 2.6 5.3 5.9.9-4.2 4.1 1 5.8-5.3-2.8-5.3 2.8 1-5.8L3.5 10l5.9-.9L12 3.8Z"/>',
		'clock'       => '<circle cx="12" cy="12" r="9"/><path d="M12 7v5.3l3.4 2"/>',
		'truck'       => '<path d="M2.5 6.5h11v10h-11z"/><path d="M13.5 10h4l3.5 3.2v3.3h-7.5"/><circle cx="6.5" cy="18" r="1.8"/><circle cx="17" cy="18" r="1.8"/>',
	);
}
