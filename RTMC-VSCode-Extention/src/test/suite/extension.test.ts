import * as assert from 'assert';
import * as vscode from 'vscode';

suite('Extension Test Suite', () => {
  vscode.window.showInformationMessage('Start all tests.');

  test('Sample test', () => {
    assert.strictEqual(-1, [1, 2, 3].indexOf(5));
    assert.strictEqual(-1, [1, 2, 3].indexOf(0));
  });

  test('Extension should be present', () => {
    assert.ok(vscode.extensions.getExtension('rtmc-dev.rtmc-language-support'));
  });

  test('Extension should activate', async () => {
    const extension = vscode.extensions.getExtension('rtmc-dev.rtmc-language-support');
    if (extension) {
      await extension.activate();
      assert.ok(extension.isActive);
    }
  });
});
