import * as vscode from 'vscode';
import * as path from 'path';
import { exec, spawn } from 'child_process';
import { promisify } from 'util';

const execAsync = promisify(exec);

export function activate(context: vscode.ExtensionContext) {
    console.log('RTMC Language Support extension is now active!');

    // Register commands
    const compileCommand = vscode.commands.registerCommand('rtmc.compile', async () => {
        await compileRTMC();
    });

    const runCommand = vscode.commands.registerCommand('rtmc.run', async () => {
        await runRTMC();
    });

    const debugCommand = vscode.commands.registerCommand('rtmc.debug', async () => {
        await debugRTMC();
    });

    // Register language configuration
    const rtmcProvider = new RTMCLanguageProvider();
    const completionProvider = vscode.languages.registerCompletionItemProvider(
        'rtmc',
        rtmcProvider,
        '.',
        '<'
    );

    const hoverProvider = vscode.languages.registerHoverProvider('rtmc', rtmcProvider);

    // Register status bar
    const statusBarItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 100);
    statusBarItem.text = "$(gear) RTMC";
    statusBarItem.tooltip = "RTMC Language Support";
    statusBarItem.command = 'rtmc.compile';
    statusBarItem.show();

    // Add all disposables to context
    context.subscriptions.push(
        compileCommand,
        runCommand,
        debugCommand,
        completionProvider,
        hoverProvider,
        statusBarItem
    );

    // Show welcome message
    vscode.window.showInformationMessage('RTMC Language Support loaded! Ready to compile and run .rtmc files.');
}

export function deactivate() {}

class RTMCLanguageProvider implements vscode.CompletionItemProvider, vscode.HoverProvider {
    
    provideCompletionItems(
        document: vscode.TextDocument,
        position: vscode.Position,
        token: vscode.CancellationToken,
        context: vscode.CompletionContext
    ): vscode.ProviderResult<vscode.CompletionItem[] | vscode.CompletionList> {
        
        const items: vscode.CompletionItem[] = [];
        
        // RTOS Functions
        const rtosFunctions = [
            'StartTask', 'RTOS_DELAY_MS', 'RTOS_SEMAPHORE_CREATE', 'RTOS_SEMAPHORE_TAKE', 
            'RTOS_SEMAPHORE_GIVE', 'RTOS_YIELD', 'RTOS_SUSPEND_TASK', 'RTOS_RESUME_TASK'
        ];
        
        rtosFunctions.forEach(func => {
            const item = new vscode.CompletionItem(func, vscode.CompletionItemKind.Function);
            if (func === 'StartTask') {
                item.insertText = new vscode.SnippetString('StartTask(${1:stack_size}, ${2:core}, ${3:priority}, ${4:task_id}, ${5:function_name});');
                item.documentation = new vscode.MarkdownString(
                    'Create and start a new RTMC task\n\n' +
                    '- stack_size: Size of the task\'s stack in bytes\n' +
                    '- core: CPU core to run the task (0 or 1)\n' +
                    '- priority: Task priority level (0-31)\n' +
                    '- task_id: Unique identifier for the task\n' +
                    '- function_name: The task function to execute'
                );
            } else {
                item.insertText = new vscode.SnippetString(`${func}($1)`);
                item.documentation = new vscode.MarkdownString(`RTOS function: ${func}`);
            }
            items.push(item);
        });
        
        // Hardware Functions
        const hwFunctions = [
            'HW_GPIO_INIT', 'HW_GPIO_SET', 'HW_GPIO_GET',
            'HW_TIMER_INIT', 'HW_TIMER_START', 'HW_TIMER_STOP', 'HW_TIMER_SET_PWM_DUTY',
            'HW_ADC_INIT', 'HW_ADC_READ',
            'HW_UART_WRITE', 'HW_SPI_TRANSFER', 'HW_I2C_WRITE', 'HW_I2C_READ'
        ];
        
        hwFunctions.forEach(func => {
            const item = new vscode.CompletionItem(func, vscode.CompletionItemKind.Function);
            item.insertText = new vscode.SnippetString(`${func}($1)`);
            item.documentation = new vscode.MarkdownString(`Hardware function: ${func}`);
            items.push(item);
        });
        
        // Debug Functions
        const debugFunctions = ['DBG_PRINT', 'DBG_BREAKPOINT'];
        debugFunctions.forEach(func => {
            const item = new vscode.CompletionItem(func, vscode.CompletionItemKind.Function);
            item.insertText = new vscode.SnippetString(`${func}($1)`);
            item.documentation = new vscode.MarkdownString(`Debug function: ${func}`);
            items.push(item);
        });
        
        // Keywords
        const keywords = [
            'StartTask', 'struct', 'int', 'float', 'char', 'bool', 'void', 'const',
            'if', 'else', 'while', 'for', 'break', 'continue', 'return',
            'import', 'send', 'recv', 'true', 'false', 'static'
        ];
        
        keywords.forEach(keyword => {
            const item = new vscode.CompletionItem(keyword, vscode.CompletionItemKind.Keyword);
            item.documentation = new vscode.MarkdownString(`RTMC keyword: ${keyword}`);
            items.push(item);
        });
        
        return items;
    }
    
    provideHover(
        document: vscode.TextDocument,
        position: vscode.Position,
        token: vscode.CancellationToken
    ): vscode.ProviderResult<vscode.Hover> {
        
        const range = document.getWordRangeAtPosition(position);
        const word = document.getText(range);
        
        const hoverInfo = this.getHoverInfo(word);
        if (hoverInfo) {
            return new vscode.Hover(hoverInfo);
        }
        
        return null;
    }
    
    private getHoverInfo(word: string): vscode.MarkdownString | null {
        const info: { [key: string]: string } = {
            'StartTask': 'Create and start a new RTMC task: `StartTask(stack_size, core, priority, task_id, function_name)`\n\n- stack_size: Size of the task\'s stack in bytes\n- core: CPU core to run the task (0 or 1)\n- priority: Task priority level (0-31)\n- task_id: Unique identifier for the task\n- function_name: The task function to execute',
            'RTOS_DELAY_MS': 'Delay execution for specified milliseconds: `RTOS_DELAY_MS(ms)`',
            'RTOS_SEMAPHORE_CREATE': 'Create a binary semaphore: `RTOS_SEMAPHORE_CREATE()`',
            'RTOS_SEMAPHORE_TAKE': 'Take a semaphore with timeout: `RTOS_SEMAPHORE_TAKE(semaphore, timeout)`',
            'RTOS_SEMAPHORE_GIVE': 'Give/release a semaphore: `RTOS_SEMAPHORE_GIVE(semaphore)`',
            'HW_GPIO_INIT': 'Initialize GPIO pin: `HW_GPIO_INIT(pin, direction)` - direction: 0=input, 1=output',
            'HW_GPIO_SET': 'Set GPIO pin value: `HW_GPIO_SET(pin, value)` - value: 0=low, 1=high',
            'HW_GPIO_GET': 'Read GPIO pin value: `HW_GPIO_GET(pin)` - returns 0 or 1',
            'HW_ADC_INIT': 'Initialize ADC pin: `HW_ADC_INIT(pin)`',
            'HW_ADC_READ': 'Read ADC value: `HW_ADC_READ(pin)` - returns 0-4095',
            'HW_TIMER_INIT': 'Initialize timer: `HW_TIMER_INIT(timer_id, frequency)`',
            'HW_TIMER_SET_PWM_DUTY': 'Set PWM duty cycle: `HW_TIMER_SET_PWM_DUTY(timer_id, duty_cycle)`',
            'HW_UART_WRITE': 'Write to UART: `HW_UART_WRITE(message)`',
            'DBG_PRINT': 'Print debug message: `DBG_PRINT(message)`',
            'DBG_BREAKPOINT': 'Set debug breakpoint: `DBG_BREAKPOINT()`',
            'struct': 'Define a structure: `struct Name { ... };` - supports bitfields with colon syntax',
            'import': 'Import another RTMC file: `#include "filename.rtmc";`'
        };
        
        if (info[word]) {
            return new vscode.MarkdownString(info[word]);
        }
        
        return null;
    }
}

async function compileRTMC(): Promise<void> {
    const activeEditor = vscode.window.activeTextEditor;
    if (!activeEditor) {
        vscode.window.showErrorMessage('No active RTMC file to compile');
        return;
    }

    const filePath = activeEditor.document.fileName;
    if (!filePath.endsWith('.rtmc')) {
        vscode.window.showErrorMessage('Active file is not an RTMC file');
        return;
    }

    const config = vscode.workspace.getConfiguration('rtmc');
    const pythonPath = config.get<string>('compilerPath') || 'python';
    const compilerScript = config.get<string>('compilerScript');

    if (!compilerScript) {
        vscode.window.showErrorMessage('Please set the path to RTMC compiler in settings (rtmc.compilerScript)');
        return;
    }

    const outputPath = filePath.replace('.rtmc', '.vmb');
    const command = `"${pythonPath}" "${compilerScript}" "${filePath}" -o "${outputPath}"`;

    try {
        vscode.window.showInformationMessage('Compiling RTMC file...');
        const { stdout, stderr } = await execAsync(command);
        
        if (stderr) {
            vscode.window.showErrorMessage(`Compilation error: ${stderr}`);
        } else {
            vscode.window.showInformationMessage(`Compilation successful! Output: ${outputPath}`);
        }
        
        // Show output in terminal
        const terminal = vscode.window.createTerminal('RTMC Compiler');
        terminal.sendText(command);
        terminal.show();
        
    } catch (error) {
        vscode.window.showErrorMessage(`Compilation failed: ${error}`);
    }
}

async function runRTMC(): Promise<void> {
    const activeEditor = vscode.window.activeTextEditor;
    if (!activeEditor) {
        vscode.window.showErrorMessage('No active RTMC file to run');
        return;
    }

    const filePath = activeEditor.document.fileName;
    let vmbPath: string;
    
    if (filePath.endsWith('.rtmc')) {
        // Compile first, then run
        await compileRTMC();
        vmbPath = filePath.replace('.rtmc', '.vmb');
    } else if (filePath.endsWith('.vmb')) {
        vmbPath = filePath;
    } else {
        vscode.window.showErrorMessage('Active file is not an RTMC or VMB file');
        return;
    }

    const config = vscode.workspace.getConfiguration('rtmc');
    const pythonPath = config.get<string>('compilerPath') || 'python';
    const vmRunnerScript = config.get<string>('vmRunnerScript');

    if (!vmRunnerScript) {
        vscode.window.showErrorMessage('Please set the path to RTMC VM runner in settings (rtmc.vmRunnerScript)');
        return;
    }

    const debugMode = config.get<boolean>('enableDebugMode') ? '--debug' : '';
    const command = `"${pythonPath}" "${vmRunnerScript}" "${vmbPath}" ${debugMode}`;

    try {
        vscode.window.showInformationMessage('Running RTMC program...');
        
        const terminal = vscode.window.createTerminal('RTMC Runner');
        terminal.sendText(command);
        terminal.show();
        
    } catch (error) {
        vscode.window.showErrorMessage(`Failed to run RTMC program: ${error}`);
    }
}

async function debugRTMC(): Promise<void> {
    const activeEditor = vscode.window.activeTextEditor;
    if (!activeEditor) {
        vscode.window.showErrorMessage('No active RTMC file to debug');
        return;
    }

    const filePath = activeEditor.document.fileName;
    let vmbPath: string;
    
    if (filePath.endsWith('.rtmc')) {
        // Compile first, then debug
        await compileRTMC();
        vmbPath = filePath.replace('.rtmc', '.vmb');
    } else if (filePath.endsWith('.vmb')) {
        vmbPath = filePath;
    } else {
        vscode.window.showErrorMessage('Active file is not an RTMC or VMB file');
        return;
    }

    const config = vscode.workspace.getConfiguration('rtmc');
    const pythonPath = config.get<string>('compilerPath') || 'python';
    const vmRunnerScript = config.get<string>('vmRunnerScript');

    if (!vmRunnerScript) {
        vscode.window.showErrorMessage('Please set the path to RTMC VM runner in settings (rtmc.vmRunnerScript)');
        return;
    }

    const command = `"${pythonPath}" "${vmRunnerScript}" "${vmbPath}" --debug --trace`;

    try {
        vscode.window.showInformationMessage('Debugging RTMC program...');
        
        const terminal = vscode.window.createTerminal('RTMC Debugger');
        terminal.sendText(command);
        terminal.show();
        
    } catch (error) {
        vscode.window.showErrorMessage(`Failed to debug RTMC program: ${error}`);
    }
}
