<?php
/**
 * detail.php — お問い合わせ詳細・ステータス変更・削除
 */
declare(strict_types=1);
require __DIR__ . '/_bootstrap.php';
require_login();

$id = (int) ($_GET['id'] ?? 0);

/* 更新・削除 */
if ($_SERVER['REQUEST_METHOD'] === 'POST' && csrf_check()) {
    $act = $_POST['action'] ?? '';
    if ($act === 'status') {
        $st = in_array($_POST['status'] ?? '', ['new', 'in_progress', 'done'], true) ? $_POST['status'] : 'new';
        db()->prepare('UPDATE contacts SET status=? WHERE id=?')->execute([$st, $id]);
        header('Location: detail.php?id=' . $id . '&updated=1');
        exit;
    }
    if ($act === 'delete') {
        db()->prepare('DELETE FROM contacts WHERE id=?')->execute([$id]);
        header('Location: index.php?deleted=1');
        exit;
    }
}

$stmt = db()->prepare('SELECT * FROM contacts WHERE id=?');
$stmt->execute([$id]);
$r = $stmt->fetch();
?>
<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="robots" content="noindex,nofollow">
<title>詳細｜お問い合わせ管理</title>
<link rel="stylesheet" href="admin.css">
</head>
<body>
<div class="topbar">
  <div class="wrap">
    <span class="brand"><a href="index.php" style="color:#fff">← 一覧へ戻る</a></span>
    <span><?= h($_SESSION['admin']) ?> ｜ <a href="logout.php">ログアウト</a></span>
  </div>
</div>
<div class="wrap">
<?php if (!$r): ?>
  <div class="card"><p>該当のお問い合わせが見つかりません。</p></div>
<?php else: ?>
  <?php if (isset($_GET['updated'])): ?><div class="alert ok">ステータスを更新しました。</div><?php endif; ?>
  <div class="card">
    <div class="row" style="justify-content:space-between">
      <h1 style="margin:0">お問い合わせ #<?= (int) $r['id'] ?></h1>
      <span class="badge <?= h($r['status']) ?>"><?= h(status_label($r['status'])) ?></span>
    </div>

    <dl class="kv">
      <dt>受信日時</dt><dd><?= h($r['created_at']) ?></dd>
      <dt>お名前</dt><dd><?= h($r['name']) ?></dd>
      <dt>会社・団体</dt><dd><?= h($r['company']) ?: '—' ?></dd>
      <dt>メール</dt><dd><a href="mailto:<?= h($r['email']) ?>"><?= h($r['email']) ?></a></dd>
      <dt>電話</dt><dd><?= h($r['phone']) ?: '—' ?></dd>
      <dt>種別</dt><dd><?= h($r['category']) ?: '—' ?></dd>
      <dt>IP</dt><dd class="muted"><?= h($r['ip']) ?></dd>
    </dl>

    <label>お問い合わせ内容</label>
    <div class="msg-box"><?= h($r['message']) ?></div>

    <hr style="border:0;border-top:1px solid var(--bd);margin:1.5rem 0">

    <div class="row" style="justify-content:space-between">
      <form method="post" class="row">
        <input type="hidden" name="csrf" value="<?= h(csrf_token()) ?>">
        <input type="hidden" name="action" value="status">
        <label style="margin:0">状態を変更</label>
        <select name="status" style="width:auto">
          <option value="new" <?= $r['status'] === 'new' ? 'selected' : '' ?>>未対応</option>
          <option value="in_progress" <?= $r['status'] === 'in_progress' ? 'selected' : '' ?>>対応中</option>
          <option value="done" <?= $r['status'] === 'done' ? 'selected' : '' ?>>完了</option>
        </select>
        <button class="btn btn--sm" type="submit">更新</button>
      </form>

      <form method="post" onsubmit="return confirm('このお問い合わせを削除します。よろしいですか？');">
        <input type="hidden" name="csrf" value="<?= h(csrf_token()) ?>">
        <input type="hidden" name="action" value="delete">
        <button class="btn btn--danger btn--sm" type="submit">削除</button>
      </form>
    </div>
  </div>
  <p style="margin-top:1rem"><a href="mailto:<?= h($r['email']) ?>?subject=Re:%20お問い合わせ%20%23<?= (int) $r['id'] ?>" class="btn btn--ghost btn--sm">メールで返信する</a></p>
<?php endif; ?>
</div>
</body>
</html>
