/**
 * コレクションページ用のJavaScript
 */

function changeSort(sortValue) {
    const currentUrl = new URL(window.location);
    if (sortValue === 'default') {
        currentUrl.searchParams.delete('sort');
    } else {
        currentUrl.searchParams.set('sort', sortValue);
    }
    // ページネーションをリセット
    currentUrl.searchParams.delete('page');
    window.location.href = currentUrl.toString();
} 