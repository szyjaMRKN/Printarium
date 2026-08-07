<?php
/**
 * Shortcode'y motywu: FAQ, formularz kontaktowy, kafle kategorii, pasek atutów.
 *
 * @package Printarium
 */

defined( 'ABSPATH' ) || exit;

/**
 * Domyślna lista pytań i odpowiedzi.
 *
 * Można nadpisać filtrem `printarium_faq_items`.
 *
 * @return array
 */
function printarium_faq_items() {
	return apply_filters(
		'printarium_faq_items',
		array(
			array(
				'q' => __( 'Jak dobrać formikarium do gatunku mrówek?', 'printarium' ),
				'a' => __( 'Dobór formikarium zależy od gatunku mrówek oraz wielkości kolonii. Dla małych kolonii polecamy formikaria modułowe w rozmiarze M, a dla większych – L i XL. W razie wątpliwości skontaktuj się z nami, chętnie doradzimy.', 'printarium' ),
			),
			array(
				'q' => __( 'Czy wykonujecie projekty na zamówienie?', 'printarium' ),
				'a' => __( 'Tak. Realizujemy projekty indywidualne – od pojedynczych modułów po kompletne zestawy hodowlane. Opisz swój pomysł w formularzu kontaktowym, a przygotujemy wycenę wraz z wizualizacją.', 'printarium' ),
			),
			array(
				'q' => __( 'Jak długo trwa realizacja zamówienia?', 'printarium' ),
				'a' => __( 'Produkty dostępne w magazynie wysyłamy w ciągu 1–3 dni roboczych. Projekty na zamówienie realizujemy zwykle w 7–21 dni roboczych, w zależności od stopnia złożoności.', 'printarium' ),
			),
			array(
				'q' => __( 'Z jakich materiałów wykonane są produkty?', 'printarium' ),
				'a' => __( 'Korzystamy z filamentów PLA i PETG oraz z akrylu (PMMA). Wszystkie materiały mające kontakt ze zwierzętami są bezpieczne i nie zawierają szkodliwych domieszek.', 'printarium' ),
			),
			array(
				'q' => __( 'Czy wysyłacie zwierzęta?', 'printarium' ),
				'a' => __( 'Tak, wysyłamy je w specjalnie przygotowanych opakowaniach transportowych, wyłącznie w bezpiecznych warunkach pogodowych. Szczegóły ustalamy indywidualnie przed wysyłką.', 'printarium' ),
			),
		)
	);
}

/**
 * Shortcode [printarium_faq] – akordeon z pytaniami.
 *
 * @param array $atts Atrybuty: single (true/false).
 * @return string
 */
function printarium_faq_shortcode( $atts ) {
	$atts = shortcode_atts( array( 'single' => 'true' ), $atts, 'printarium_faq' );

	$items = printarium_faq_items();

	if ( empty( $items ) ) {
		return '';
	}

	ob_start();
	?>
	<div class="pr-accordion" data-single="<?php echo esc_attr( $atts['single'] ); ?>">
		<?php foreach ( $items as $index => $item ) : ?>
			<?php $panel_id = 'pr-faq-' . wp_unique_id(); ?>
			<div class="pr-accordion__item<?php echo 0 === $index ? ' is-open' : ''; ?>">
				<h3 style="margin:0">
					<button type="button" class="pr-accordion__trigger" aria-expanded="<?php echo 0 === $index ? 'true' : 'false'; ?>" aria-controls="<?php echo esc_attr( $panel_id ); ?>">
						<span><?php echo esc_html( $item['q'] ); ?></span>
						<span class="pr-accordion__icon"><?php printarium_icon( 'chevron', 22 ); ?></span>
					</button>
				</h3>
				<div class="pr-accordion__panel" id="<?php echo esc_attr( $panel_id ); ?>">
					<div>
						<div class="pr-accordion__content"><?php echo wp_kses_post( wpautop( $item['a'] ) ); ?></div>
					</div>
				</div>
			</div>
		<?php endforeach; ?>
	</div>
	<?php
	return ob_get_clean();
}
add_shortcode( 'printarium_faq', 'printarium_faq_shortcode' );

/**
 * Shortcode [printarium_categories] – kafle kategorii sklepu.
 *
 * @param array $atts Atrybuty: limit.
 * @return string
 */
function printarium_categories_shortcode( $atts ) {
	$atts = shortcode_atts( array( 'limit' => 5 ), $atts, 'printarium_categories' );

	$terms = printarium_get_shop_categories( (int) $atts['limit'] );

	if ( empty( $terms ) ) {
		return '';
	}

	ob_start();
	?>
	<div class="category-grid">
		<?php foreach ( $terms as $term ) : ?>
			<?php
			$link = get_term_link( $term );
			if ( is_wp_error( $link ) ) {
				continue;
			}
			?>
			<a class="category-card" href="<?php echo esc_url( $link ); ?>">
				<h3 class="category-card__title"><?php echo esc_html( $term->name ); ?></h3>
				<figure class="category-card__figure"><?php echo printarium_category_thumbnail( $term ); // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped ?></figure>
				<span class="category-card__arrow" aria-hidden="true"><?php printarium_icon( 'arrow-right', 20 ); ?></span>
			</a>
		<?php endforeach; ?>
	</div>
	<?php
	return ob_get_clean();
}
add_shortcode( 'printarium_categories', 'printarium_categories_shortcode' );

/**
 * Shortcode [printarium_contact_form] – prosty formularz zapytania.
 *
 * Wysyła wiadomość na adres administratora (lub `to="..."`).
 *
 * @param array $atts Atrybuty: to, title.
 * @return string
 */
function printarium_contact_form_shortcode( $atts ) {
	$atts = shortcode_atts(
		array(
			'to'    => '',
			'title' => '',
		),
		$atts,
		'printarium_contact_form'
	);

	$status = isset( $_GET['printarium_contact'] ) ? sanitize_key( wp_unslash( $_GET['printarium_contact'] ) ) : ''; // phpcs:ignore WordPress.Security.NonceVerification.Recommended

	ob_start();
	?>
	<div class="printarium-contact-form card">
		<?php if ( $atts['title'] ) : ?>
			<h3 class="mt-0"><?php echo esc_html( $atts['title'] ); ?></h3>
		<?php endif; ?>

		<?php if ( 'sent' === $status ) : ?>
			<div class="pr-alert pr-alert--success">
				<?php printarium_icon( 'check', 20 ); ?>
				<span><?php esc_html_e( 'Zapytanie zostało wysłane. Odpowiemy najszybciej, jak to możliwe.', 'printarium' ); ?></span>
			</div>
		<?php elseif ( 'error' === $status ) : ?>
			<div class="pr-alert pr-alert--error">
				<?php printarium_icon( 'error', 20 ); ?>
				<span><?php esc_html_e( 'Nie udało się wysłać wiadomości. Spróbuj ponownie lub napisz do nas bezpośrednio.', 'printarium' ); ?></span>
			</div>
		<?php elseif ( 'invalid' === $status ) : ?>
			<div class="pr-alert pr-alert--error">
				<?php printarium_icon( 'warning', 20 ); ?>
				<span><?php esc_html_e( 'Uzupełnij wszystkie wymagane pola i podaj poprawny adres e-mail.', 'printarium' ); ?></span>
			</div>
		<?php endif; ?>

		<form method="post" action="<?php echo esc_url( admin_url( 'admin-post.php' ) ); ?>" enctype="multipart/form-data">
			<input type="hidden" name="action" value="printarium_contact">
			<input type="hidden" name="printarium_redirect" value="<?php echo esc_url( get_permalink() ); ?>">
			<input type="hidden" name="printarium_to" value="<?php echo esc_attr( $atts['to'] ); ?>">
			<?php wp_nonce_field( 'printarium_contact', 'printarium_contact_nonce' ); ?>

			<p class="printarium-hp" aria-hidden="true" style="position:absolute;left:-9999px">
				<label for="printarium-website"><?php esc_html_e( 'Zostaw to pole puste', 'printarium' ); ?></label>
				<input type="text" id="printarium-website" name="printarium_website" tabindex="-1" autocomplete="off">
			</p>

			<p>
				<label for="printarium-name"><?php esc_html_e( 'Imię i nazwisko', 'printarium' ); ?> <span class="text-green">*</span></label>
				<input type="text" id="printarium-name" name="printarium_name" placeholder="<?php esc_attr_e( 'Imię i nazwisko', 'printarium' ); ?>" required>
			</p>

			<p>
				<label for="printarium-email"><?php esc_html_e( 'Adres e-mail', 'printarium' ); ?> <span class="text-green">*</span></label>
				<input type="email" id="printarium-email" name="printarium_email" placeholder="adres@email.pl" required>
			</p>

			<p>
				<label for="printarium-message"><?php esc_html_e( 'Opisz swój projekt', 'printarium' ); ?> <span class="text-green">*</span></label>
				<textarea id="printarium-message" name="printarium_message" placeholder="<?php esc_attr_e( 'Opisz swój projekt', 'printarium' ); ?>" required></textarea>
			</p>

			<label class="pr-dropzone" for="printarium-file">
				<?php printarium_icon( 'upload', 28 ); ?>
				<span>
					<span class="pr-dropzone__title"><?php esc_html_e( 'Dodaj zdjęcie lub projekt', 'printarium' ); ?></span><br>
					<span class="pr-dropzone__hint"><?php esc_html_e( 'Przeciągnij plik tutaj lub kliknij, aby wybrać', 'printarium' ); ?></span>
				</span>
				<input type="file" id="printarium-file" name="printarium_file" accept="image/*,.pdf,.stl,.zip">
			</label>

			<p class="mt-3 mb-0">
				<button type="submit" class="btn btn--primary btn--block"><?php esc_html_e( 'Wyślij zapytanie', 'printarium' ); ?></button>
			</p>
		</form>
	</div>
	<?php
	return ob_get_clean();
}
add_shortcode( 'printarium_contact_form', 'printarium_contact_form_shortcode' );

/**
 * Obsługa wysyłki formularza kontaktowego.
 */
function printarium_handle_contact_form() {
	$redirect = isset( $_POST['printarium_redirect'] ) ? esc_url_raw( wp_unslash( $_POST['printarium_redirect'] ) ) : home_url( '/' );

	if ( ! isset( $_POST['printarium_contact_nonce'] ) || ! wp_verify_nonce( sanitize_text_field( wp_unslash( $_POST['printarium_contact_nonce'] ) ), 'printarium_contact' ) ) {
		wp_safe_redirect( add_query_arg( 'printarium_contact', 'error', $redirect ) );
		exit;
	}

	// Pułapka na boty – wypełnione pole oznacza spam; udajemy sukces.
	if ( ! empty( $_POST['printarium_website'] ) ) {
		wp_safe_redirect( add_query_arg( 'printarium_contact', 'sent', $redirect ) );
		exit;
	}

	$name    = isset( $_POST['printarium_name'] ) ? sanitize_text_field( wp_unslash( $_POST['printarium_name'] ) ) : '';
	$email   = isset( $_POST['printarium_email'] ) ? sanitize_email( wp_unslash( $_POST['printarium_email'] ) ) : '';
	$message = isset( $_POST['printarium_message'] ) ? sanitize_textarea_field( wp_unslash( $_POST['printarium_message'] ) ) : '';

	if ( ! $name || ! is_email( $email ) || ! $message ) {
		wp_safe_redirect( add_query_arg( 'printarium_contact', 'invalid', $redirect ) );
		exit;
	}

	$to = isset( $_POST['printarium_to'] ) ? sanitize_email( wp_unslash( $_POST['printarium_to'] ) ) : '';

	if ( ! is_email( $to ) ) {
		$to = printarium_option( 'printarium_contact_email' );
	}
	if ( ! is_email( $to ) ) {
		$to = get_option( 'admin_email' );
	}

	$subject = sprintf(
		/* translators: %s: nazwa serwisu. */
		__( '[%s] Nowe zapytanie ze strony', 'printarium' ),
		get_bloginfo( 'name' )
	);

	$body = sprintf(
		"%s: %s\n%s: %s\n\n%s:\n%s\n",
		__( 'Imię i nazwisko', 'printarium' ),
		$name,
		__( 'E-mail', 'printarium' ),
		$email,
		__( 'Wiadomość', 'printarium' ),
		$message
	);

	$attachments = array();

	if ( ! empty( $_FILES['printarium_file']['name'] ) && empty( $_FILES['printarium_file']['error'] ) ) {
		require_once ABSPATH . 'wp-admin/includes/file.php';
		require_once ABSPATH . 'wp-admin/includes/media.php';
		require_once ABSPATH . 'wp-admin/includes/image.php';

		$attachment_id = media_handle_upload( 'printarium_file', 0 );

		if ( ! is_wp_error( $attachment_id ) ) {
			$path = get_attached_file( $attachment_id );
			if ( $path ) {
				$attachments[] = $path;
			}
			$body .= "\n" . __( 'Załącznik', 'printarium' ) . ': ' . wp_get_attachment_url( $attachment_id ) . "\n";
		}
	}

	$headers = array(
		'Content-Type: text/plain; charset=UTF-8',
		'Reply-To: ' . $name . ' <' . $email . '>',
	);

	$sent = wp_mail( $to, $subject, $body, $headers, $attachments );

	wp_safe_redirect( add_query_arg( 'printarium_contact', $sent ? 'sent' : 'error', $redirect ) );
	exit;
}
add_action( 'admin_post_printarium_contact', 'printarium_handle_contact_form' );
add_action( 'admin_post_nopriv_printarium_contact', 'printarium_handle_contact_form' );
