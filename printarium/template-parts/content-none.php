<?php
/**
 * Komunikat „brak wyników”.
 *
 * @package Printarium
 */

defined( 'ABSPATH' ) || exit;
?>
<div class="no-results">
	<span class="no-results__icon"><?php printarium_icon( 'box', 64 ); ?></span>
	<h2 class="no-results__title"><?php esc_html_e( 'Nie znaleziono wyników', 'printarium' ); ?></h2>
	<p class="no-results__text"><?php esc_html_e( 'Spróbuj zmienić zapytanie lub usunąć filtry.', 'printarium' ); ?></p>

	<div class="container container--narrow">
		<?php get_search_form(); ?>
	</div>
</div>
