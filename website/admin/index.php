<?php
/**
 * index.php — 管理画面：ログイン ＆ お問い合わせ一覧
 */
declare(strict_types=1);
require __DIR__ . '/_bootstrap.php';

$loginError = '';

/* ----- ログイン処理 ----- */
if (($_POST['action'] ?? '') === 'login') {
    $now = time();
    // 簡易ブルートフォース対策：5回失敗で30秒ロック
    $lock = $_SESSION['login_lock'] ?? 0;
    if ($now < $lock) {
        $loginError = 'ログイン試行が多すぎます。しばらく待って再度お試しください。';
    } else {
        $u = (string) ($_POST['username'] ?? '');
        $p = (string) ($_POST['password'] ?? '');
        if (hash_equals(ADMIN_USER, $u) && password_verify($p, ADMIN_PASS_HASH)) {
            session_regenerate_id(true);
            $_SESSION['admin'] = $u;
            unset($_SESSION['login_fail'], $_SESSION['login_lock']);
            header('Location: index.php');
            exit;
        }
        $_SESSION['login_fail'] = ($_SESSION['login_fail'] ?? 0) + 1;
        if ($_SESSION['login_fail'] >= 5) {
            $_SESSION['login_lock'] = $now + 30;
            $_SESSION['login_fail'] = 0;
        }
        $loginError = 'ユーザー名またはパスワードが違います。';
    }
}

/* ----- ステータス更新 / 削除（一覧から） ----- */
if (is_logged_in() && $_SERVER['REQUEST_METHOD'] === 'POST' && csrf_check()) {
    $act = $_POST['action'] ?? '';
    $id  = (int) ($_POST['id'] ?? 0);
    if ($act === 'status' && $id) {
        $st = in_array($_POST['status'] ?? '', ['new', 'in_progress', 'done'], true) ? $_POST['status'] : 'new';
        $stmt = db()->prepare('UPDATE contacts SET status=? WHERE id=?');
        $stmt->execute([$st, $id]);
        header('Location: ' . ($_POST['back'] ?? 'index.php'));
        exit;
    }
    if ($act === 'delete' && $id) {
        db()->prepare('DELETE FROM contacts WHERE id=?')->execute([$id]);
        header('Location: ' . ($_POST['back'] ?? 'index.php'));
        exit;
    }
}
?>
<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="robots" content="noindex,nofollow">
<title>お問い合わせ管理｜Rion Lab Japan</title>
<link rel="stylesheet" href="admin.css">
</head>
<body>
<?php if (!is_logged_in()): ?>
  <!-- ===== ログイン画面 ===== -->
  <div class="wrap">
    <div class="card login">
      <h1>管理画面ログイン</h1>
      <?php if ($loginError): ?><div class="alert err"><?= h($loginError) ?></div><?php endif; ?>
      <form method="post">
        <input type="hidden" name="action" value="login">
        <p><label for="u">ユーザー名</label><input id="u" name="username" autocomplete="username" required></p>
        <p><label for="p">パスワード</label><input id="p" name="password" type="password" autocomplete="current-password" required></p>
        <button class="btn" type="submit">ログイン</button>
      </form>
    </div>
  </div>
<?php else:
  /* ===== 一覧 ===== */
  $q       = trim((string) ($_GET['q'] ?? ''));
  $fstatus = in_array($_GET['status'] ?? '', ['new', 'in_progress', 'done'], true) ? $_GET['status'] : '';
  $page    = max(1, (int) ($_GET['page'] ?? 1));
  $per     = 20;

  $where = []; $args = [];
  if ($q !== '') {
      $where[] = '(name LIKE ? OR email LIKE ? OR company LIKE ? OR message LIKE ?)';
      $kw = '%' . $q . '%';
      array_push($args, $kw, $kw, $kw, $kw);
  }
  if ($fstatus !== '') { $where[] = 'status = ?'; $args[] = $fstatus; }
  $wsql = $where ? ('WHERE ' . implode(' AND ', $where)) : '';

  $cnt = db()->prepare("SELECT COUNT(*) FROM contacts $wsql");
  $cnt->execute($args);
  $total = (int) $cnt->fetchColumn();
  $pages = max(1, (int) ceil($total / $per));
  $page  = min($page, $pages);
  $off   = ($page - 1) * $per;

  $sql = "SELECT * FROM contacts $wsql ORDER BY id DESC LIMIT $per OFFSET $off";
  $stmt = db()->prepare($sql);
  $stmt->execute($args);
  $rows = $stmt->fetchAll();

  $qsBase = http_build_query(array_filter(['q' => $q, 'status' => $fstatus]));
  $back   = 'index.php' . ($qsBase ? '?' . $qsBase . '&page=' . $page : '?page=' . $page);
?>
  <div class="topbar">
    <div class="wrap">
      <span class="brand">Rion Lab Japan — お問い合わせ管理</span>
      <span><?= h($_SESSION['admin']) ?> ｜ <a href="logout.php">ログアウト</a></span>
    </div>
  </div>
  <div class="wrap">
    <div class="toolbar">
      <form class="row" method="get">
        <input type="search" name="q" value="<?= h($q) ?>" placeholder="氏名・メール・会社・本文で検索" style="width:240px">
        <select name="status" style="width:auto">
          <option value="">すべての状態</option>
          <option value="new" <?= $fstatus === 'new' ? 'selected' : '' ?>>未対応</option>
          <option value="in_progress" <?= $fstatus === 'in_progress' ? 'selected' : '' ?>>対応中</option>
          <option value="done" <?= $fstatus === 'done' ? 'selected' : '' ?>>完了</option>
        </select>
        <button class="btn btn--sm" type="submit">検索</button>
        <?php if ($q || $fstatus): ?><a class="btn btn--ghost btn--sm" href="index.php">クリア</a><?php endif; ?>
      </form>
      <a class="btn btn--ghost btn--sm" href="export.php?<?= h($qsBase) ?>">CSVエクスポート</a>
    </div>

    <p class="muted">全 <?= $total ?> 件<?= ($q || $fstatus) ? '（絞り込み中）' : '' ?></p>

    <table>
      <thead>
        <tr><th>状態</th><th>日時</th><th>お名前 / 会社</th><th>種別</th><th>メール</th><th></th></tr>
      </thead>
      <tbody>
        <?php if (!$rows): ?>
          <tr><td colspan="6" class="muted" style="text-align:center;padding:2em">該当する問い合わせはありません。</td></tr>
        <?php endif; ?>
        <?php foreach ($rows as $r): ?>
          <tr>
            <td><span class="badge <?= h($r['status']) ?>"><?= h(status_label($r['status'])) ?></span></td>
            <td class="muted"><?= h($r['created_at']) ?></td>
            <td><strong><?= h($r['name']) ?></strong><br><span class="muted"><?= h($r['company']) ?></span></td>
            <td class="muted"><?= h($r['category']) ?></td>
            <td class="muted"><?= h($r['email']) ?></td>
            <td><a class="btn btn--ghost btn--sm" href="detail.php?id=<?= (int) $r['id'] ?>">詳細</a></td>
          </tr>
        <?php endforeach; ?>
      </tbody>
    </table>

    <?php if ($pages > 1): ?>
      <div class="pager">
        <?php for ($i = 1; $i <= $pages; $i++):
          $url = 'index.php?' . http_build_query(array_filter(['q' => $q, 'status' => $fstatus, 'page' => $i])); ?>
          <?php if ($i === $page): ?><span class="cur"><?= $i ?></span>
          <?php else: ?><a href="<?= h($url) ?>"><?= $i ?></a><?php endif; ?>
        <?php endfor; ?>
      </div>
    <?php endif; ?>
  </div>
<?php endif; ?>
</body>
</html>
