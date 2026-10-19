import { describe, it } from 'node:test';
import assert from 'node:assert/strict';
import readings from '../yurigana/kanji-readings.json' with { type: 'json' };
import { hideKnownRuby, isPlainReading } from './index.js';

const met = Object.fromEntries([...'本気異能宇宙人間茶学校今日一'].map((kanji) => [kanji, 10]));
const hide = (base, reading, totals = met) => hideKnownRuby(base, reading, totals, readings);

describe('hideKnownRuby', () => {
  it('hides a plain reading of kanji met often enough', () => {
    assert.equal(hide('人間', 'にんげん'), true);
    assert.equal(hide('学校', 'がっこう'), true);
    assert.equal(hide('人々', 'ひとびと'), true);
  });

  it('keeps katakana ruby', () => {
    assert.equal(hide('本気', 'マジ'), false);
    assert.equal(hide('異能', 'スキル'), false);
  });

  it('keeps hiragana ruby that is not a reading of the base', () => {
    assert.equal(hide('宇宙', 'そら'), false);
    assert.equal(hide('本気', 'まじ'), false);
    assert.equal(hide('宇宙', 'うちゅう'), true);
  });

  it('keeps jukujikun, which the per-kanji readings cannot spell', () => {
    assert.equal(hide('今日', 'きょう'), false);
  });

  it('keeps ruby with kanji and bases without kanji', () => {
    assert.equal(hide('本気', '本気'), false);
    assert.equal(hide('スキル', 'すきる'), false);
  });

  it('matches the kana of a partly kanji base', () => {
    assert.equal(hide('お茶', 'おちゃ'), true);
    assert.equal(hide('お茶', 'ちゃ'), false);
  });

  it('needs every kanji met at least ten times', () => {
    assert.equal(hide('人間', 'にんげん', { ...met, 間: 9 }), false);
    assert.equal(hideKnownRuby('人間', 'にんげん', { 人: 1, 間: 1 }, readings, 1), true);
  });
});

describe('isPlainReading', () => {
  it('allows rendaku and a final っ, and kanji outside the table never match', () => {
    assert.equal(isPlainReading('人々', 'ひとびと', readings), true);
    assert.equal(isPlainReading('学校', 'がっこう', readings), true);
    assert.equal(isPlainReading('𠮟る', 'しかる', readings), false);
  });
});
