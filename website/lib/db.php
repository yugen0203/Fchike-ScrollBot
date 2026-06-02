<?php
/**
 * db.php — SQLite 接続とスキーマ初期化
 *
 * お問い合わせフォーム・管理画面が共通で利用する。
 * MySQL へ移行する場合はこのファイルの接続部のみ差し替えればよい。
 */
declare(strict_types=1);

/** データベースファイルの場所（公開ディレクトリ外が望ましいが、ここでは data/ 配下） */
function db_path(): string
{
    $dir = __DIR__ . '/../data';
    if (!is_dir($dir)) {
        @mkdir($dir, 0775, true);
    }
    return $dir . '/contacts.sqlite';
}

/** PDO 接続（シングルトン）。初回にスキーマを作成する。 */
function db(): PDO
{
    static $pdo = null;
    if ($pdo instanceof PDO) {
        return $pdo;
    }
    $pdo = new PDO('sqlite:' . db_path(), null, null, [
        PDO::ATTR_ERRMODE            => PDO::ERRMODE_EXCEPTION,
        PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
    ]);
    $pdo->exec('PRAGMA journal_mode = WAL;');
    $pdo->exec('PRAGMA foreign_keys = ON;');

    $pdo->exec(<<<SQL
        CREATE TABLE IF NOT EXISTS contacts (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            name       TEXT    NOT NULL,
            company    TEXT    DEFAULT '',
            email      TEXT    NOT NULL,
            phone      TEXT    DEFAULT '',
            category   TEXT    DEFAULT '',
            message    TEXT    NOT NULL,
            status     TEXT    NOT NULL DEFAULT 'new',
            ip         TEXT    DEFAULT '',
            user_agent TEXT    DEFAULT '',
            created_at TEXT    NOT NULL DEFAULT (datetime('now','localtime'))
        );
    SQL);

    return $pdo;
}

/** 問い合わせを1件保存し、新規IDを返す。 */
function save_contact(array $d): int
{
    $stmt = db()->prepare(
        'INSERT INTO contacts (name, company, email, phone, category, message, ip, user_agent)
         VALUES (:name, :company, :email, :phone, :category, :message, :ip, :ua)'
    );
    $stmt->execute([
        ':name'     => $d['name'],
        ':company'  => $d['company'] ?? '',
        ':email'    => $d['email'],
        ':phone'    => $d['phone'] ?? '',
        ':category' => $d['category'] ?? '',
        ':message'  => $d['message'],
        ':ip'       => $_SERVER['REMOTE_ADDR'] ?? '',
        ':ua'       => substr($_SERVER['HTTP_USER_AGENT'] ?? '', 0, 255),
    ]);
    return (int) db()->lastInsertId();
}
