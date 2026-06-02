<?php
/**
 * export.php — お問い合わせをCSV出力（Excel対応・UTF-8 BOM）
 * 一覧の検索条件（q / status）を引き継いで出力する。
 */
declare(strict_types=1);
require __DIR__ . '/_bootstrap.php';
require_login();

$q       = trim((string) ($_GET['q'] ?? ''));
$fstatus = in_array($_GET['status'] ?? '', ['new', 'in_progress', 'done'], true) ? $_GET['status'] : '';

$where = []; $args = [];
if ($q !== '') {
    $where[] = '(name LIKE ? OR email LIKE ? OR company LIKE ? OR message LIKE ?)';
    $kw = '%' . $q . '%';
    array_push($args, $kw, $kw, $kw, $kw);
}
if ($fstatus !== '') { $where[] = 'status = ?'; $args[] = $fstatus; }
$wsql = $where ? ('WHERE ' . implode(' AND ', $where)) : '';

$stmt = db()->prepare("SELECT * FROM contacts $wsql ORDER BY id DESC");
$stmt->execute($args);

$filename = 'contacts_' . date('Ymd_His') . '.csv';
header('Content-Type: text/csv; charset=UTF-8');
header('Content-Disposition: attachment; filename="' . $filename . '"');

$out = fopen('php://output', 'w');
fwrite($out, "\xEF\xBB\xBF"); // UTF-8 BOM（Excel文字化け対策）

fputcsv($out, ['ID', '受信日時', 'ステータス', 'お名前', '会社', 'メール', '電話', '種別', '内容', 'IP']);
while ($r = $stmt->fetch()) {
    fputcsv($out, [
        $r['id'], $r['created_at'], status_label($r['status']),
        $r['name'], $r['company'], $r['email'], $r['phone'],
        $r['category'], $r['message'], $r['ip'],
    ]);
}
fclose($out);
