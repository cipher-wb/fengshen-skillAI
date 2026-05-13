// @inquirer/prompts wrapper / 统一交互风格
import { input, select, confirm } from '@inquirer/prompts';

export async function askInput({ message, default: defaultValue, validate }) {
  return await input({
    message,
    default: defaultValue,
    validate: validate || ((v) => v.trim() !== '' || '不能为空')
  });
}

export async function askSelect({ message, choices, default: defaultValue }) {
  return await select({
    message,
    choices: choices.map((c) => typeof c === 'string' ? { name: c, value: c } : c),
    default: defaultValue
  });
}

export async function askConfirm({ message, default: defaultValue = true }) {
  return await confirm({ message, default: defaultValue });
}
