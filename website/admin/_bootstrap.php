<?php
/**
 * _bootstrap.php — 管理画面の共通初期化
 * セッション開始・設定読込・認証ヘルパ・CSRF を提供する。
 */
declare(strict_types=1);

session_start();
require __DIR__ . '/../lib/db.php';

$configFile = __DIR__ . '/config.php';
if (!is_file($configFile)) {
    http_response_code(500);
    exit('管理画面が未設定です。admin/config.sample.php を config.php にコピーして設定してください。');
}
require $configFile;

/** ログイン済みか */
function is_logged_in(): bool
{
    return !empty($_SESSION['admin']);
}

/** 未ログインならログイン画面へ */
function require_login(): void
{
    if (!is_logged_in()) {
        header('Location: index.php');
        exit;
    }
}

/** CSRFトークン取得 */
function csrf_token(): string
{
    if (empty($_SESSION['admin_csrf'])) {
        $_SESSION['admin_csrf'] = bin2hex(random_bytes(32));
    }
    return $_SESSION['admin_csrf'];
}

/** CSRF検証 */
function csrf_check(): bool
{
    return isset($_POST['csrf']) && hash_equals($_SESSION['admin_csrf'] ?? '', (string) $_POST['csrf']);
}

function h(?string $s): string { return htmlspecialchars((string) $s, ENT_QUOTES, 'UTF-8'); }

/** ステータスの日本語ラベル */
function status_label(string $s): string
{
    return ['new' => '未対応', 'in_progress' => '対応中', 'done' => '完了'][$s] ?? $s;
}
