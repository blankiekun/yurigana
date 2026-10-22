"""Tests for yurigana.readings: ruby and context rules."""
import unittest

from yurigana.readings import conjugated_reading, context_reading, glued, ruby_reading, surface_reading, unlisted_reading
from yurigana.rules import DEFAULT_READINGS


class RubyReadingTest(unittest.TestCase):
    def test_only_plain_readings_listed_by_jiten(self):
        known = {('人気', 'ひとけ'), ('人気', 'にんき'), ('本気', 'まじ'), ('本気', 'ほんき'), ('宇宙', 'うちゅう')}
        hints = {0: (2, 'ひとけ'), 3: (5, 'そら'), 6: (8, 'マジ'), 9: (11, 'まじ'), 12: (13, 'ひと')}
        self.assertEqual(ruby_reading(hints, 0, '人気', '人気', known), 'ひとけ')
        self.assertIsNone(ruby_reading(hints, 3, '宇宙', '宇宙', known))  # not a reading of 宇宙
        self.assertIsNone(ruby_reading(hints, 6, '本気', '本気', known))  # katakana: flavour
        self.assertEqual(ruby_reading(hints, 9, '本気', '本気', known), 'まじ')  # Jiten lists it (accepted hole)
        self.assertIsNone(ruby_reading(hints, 12, '人気', '人気', known))  # ruby over part of the token
        self.assertIsNone(ruby_reading(hints, 1, '気', '気', known))

    def test_per_kanji_ruby_is_joined(self):
        known = {('人気', 'ひとけ'), ('人気', 'にんき')}
        self.assertEqual(ruby_reading({0: (1, 'ひと'), 1: (2, 'け')}, 0, '人気', '人気', known), 'ひとけ')
        self.assertIsNone(ruby_reading({0: (1, 'ひと'), 1: (2, 'き')}, 0, '人気', '人気', known))  # not listed
        self.assertIsNone(ruby_reading({0: (1, 'ひと'), 1: (3, 'けの')}, 0, '人気', '人気', known))  # past the token
        self.assertIsNone(ruby_reading({0: (1, 'ひと'), 1: (2, 'ケ')}, 0, '人気', '人気', known))  # katakana part

    def test_ruby_over_the_kanji_stem(self):
        known = {('行く', 'いく'), ('行く', 'ゆく'), ('上手い', 'うまい'), ('歩く', 'あるく'), ('見上げる', 'みあげる'),
                 ('子ども', 'こども'), ('魚市場', 'うおいちば')}
        self.assertEqual(ruby_reading({0: (1, 'い')}, 0, '行っ', '行く', known), 'いく')  # 行《い》った
        self.assertEqual(ruby_reading({0: (1, 'ゆ')}, 0, '行か', '行く', known), 'ゆく')
        self.assertEqual(ruby_reading({0: (2, 'うま')}, 0, '上手く', '上手い', known), 'うまい')
        self.assertEqual(ruby_reading({0: (1, 'ある')}, 0, '歩く', '歩く', known), 'あるく')
        self.assertEqual(ruby_reading({0: (1, 'み'), 1: (2, 'あ')}, 0, '見上げ', '見上げる', known), 'みあげる')
        self.assertEqual(ruby_reading({0: (1, 'こ')}, 0, '子ども', '子ども', known), 'こども')
        self.assertIsNone(ruby_reading({0: (1, 'おこな')}, 0, '行っ', '行く', known))  # おこなく: not listed
        self.assertIsNone(ruby_reading({0: (1, 'うお')}, 0, '魚市場', '魚市場', known))  # kanji left: compound
        self.assertIsNone(ruby_reading({0: (1, 'い')}, 0, '云っ', '言う', {('言う', 'いう')}))  # lemma spelled apart

    def test_large_kana_ruby(self):
        known = {('一緒', 'いっしょ'), ('目下', 'もっか'), ('目下', 'めした'), ('勝つ', 'かつ'), ('喋る', 'しゃべる')}
        self.assertEqual(ruby_reading({0: (2, 'いつしよ')}, 0, '一緒', '一緒', known), 'いっしょ')
        self.assertEqual(ruby_reading({0: (2, 'もつか')}, 0, '目下', '目下', known), 'もっか')
        self.assertEqual(ruby_reading({0: (1, 'か')}, 0, '勝つ', '勝つ', known), 'かつ')  # exact first
        self.assertEqual(ruby_reading({0: (1, 'しやべ')}, 0, '喋っ', '喋る', known), 'しゃべる')  # stem and large kana
        self.assertIsNone(ruby_reading({0: (2, 'つか')}, 0, '目下', '目下', {('目下', 'っか')}))  # never a leading っ


class ConjugatedReadingTest(unittest.TestCase):
    def test_the_one_listed_reading_that_conjugates_to_sudachis(self):
        self.assertEqual(conjugated_reading('行っ', '行く', 'いっ', ['いく', 'ゆく']), 'いく')
        self.assertEqual(conjugated_reading('行か', '行く', 'ゆか', ['いく', 'ゆく']), 'ゆく')
        self.assertEqual(conjugated_reading('行っ', '行く', 'いつ', ['いく', 'ゆく']), 'いく')  # small kana folded
        self.assertEqual(conjugated_reading('早く', '早い', 'はやく', ['はやい', 'はやーい']), 'はやい')
        self.assertEqual(conjugated_reading('上っ', '上る', 'のぼっ', ['あがる', 'のぼる']), 'のぼる')
        self.assertIsNone(conjugated_reading('行っ', '行く', 'おこなっ', ['いく', 'ゆく']))  # none matches
        self.assertIsNone(conjugated_reading('言わ', '言う', 'いわ', []))
        self.assertIsNone(conjugated_reading('云っ', '言う', 'いっ', ['いう']))  # stem spelled apart

    def test_unlisted_form_takes_sudachis_stem(self):
        for surface, form, sudachi, reading in (('泳げ', '泳げる', 'およげ', 'およげる'), ('来れ', '来れる', 'これ', 'これる'),
                                                ('思ひ', '思ふ', 'おもひ', 'おもふ'), ('悲しき', '悲し', 'かなしき', 'かなし'),
                                                ('往っ', '往く', 'いっ', 'いく')):
            self.assertEqual(unlisted_reading(surface, form, sudachi), reading, surface)
            self.assertEqual(surface_reading(surface, form, reading), sudachi, surface)  # round trip
        self.assertIsNone(unlisted_reading('云っ', '言う', 'いっ'))  # stem spelled apart
        self.assertIsNone(unlisted_reading('泳げ', '泳げる', 'およぐ'))  # Sudachi's reading doesn't end in げ
        self.assertIsNone(unlisted_reading('泳げ', '泳げる', ''))

    def test_kuru(self):
        for surface, sudachi in (('来', 'き'), ('来', 'こ'), ('来よう', 'こよう'), ('来い', 'こい'), ('来れ', 'くれ')):
            self.assertEqual(conjugated_reading(surface, '来る', sudachi, ['きたる', 'くる']), 'くる', surface)
        self.assertIsNone(conjugated_reading('来', '来る', 'き', ['きたる']))  # くる not listed

    def test_surface_reading(self):
        self.assertEqual(surface_reading('行っ', '行く', 'いく', 'た'), 'いっ')
        self.assertIsNone(surface_reading('云っ', '言う', 'いう'))
        for surface, after, expected in (('来', 'た。', 'き'), ('来', 'ます', 'き'), ('来', 'ながら', 'き'), ('来', 'なさい', 'き'),
                                         ('来', 'ない', 'こ'), ('来', 'なきゃ', 'こ'), ('来い', '', 'こい'), ('来よう', '', 'こよう'),
                                         ('来', 'られる', 'こ'), ('来れ', 'ば', 'くれ'), ('来れ', 'る', 'これ'), ('来', '。', 'き')):
            self.assertEqual(surface_reading(surface, '来る', 'くる', after), expected, surface + after)
        self.assertEqual(surface_reading('来る', '来る', 'きたる'), 'きたる')


class ContextReadingTest(unittest.TestCase):
    known = {('人気', 'ひとけ'), ('人気', 'にんき'), ('明日', 'あした'), ('明日', 'あす'), ('上手', 'かみて'),
             ('今日', 'こんにち'), ('他', 'た'), ('何', 'なに'), ('何', 'なん'),
             ('中', 'じゅう'), ('中', 'ちゅう'),
             ('種', 'しゅ'), ('下', 'した'), ('下', 'もと'), ('音', 'ね'), ('風', 'ふう'), ('風', 'かぜ'),
             ('方', 'かた'), ('方', 'ほう'), ('間', 'ま'), ('間', 'あいだ'), ('後', 'あと'),
             ('今', 'いま'), ('今', 'こん'), ('外', 'ほか'), ('外', 'そと'), ('床', 'とこ'), ('床', 'ゆか'), ('君', 'ぎみ'),
             ('君', 'くん'), ('尼', 'あま'), ('金', 'きん'), ('金', 'かね')}

    def reading(self, text, form, surface=None, known=None):
        return context_reading(text, text.index(form), surface or form, form, self.known if known is None else known)

    def test_rules(self):
        self.assertEqual(self.reading('夜の公園は人気がなく、', '人気'), 'ひとけ')
        self.assertIsNone(self.reading('彼は人気者だ。', '人気'))  # Sudachi's reading stays
        self.assertEqual(self.reading('役者が舞台の上手から', '上手'), 'かみて')  # text before
        self.assertEqual(self.reading('今日に至るまで', '今日'), 'こんにち')
        self.assertEqual(self.reading('その他の項目', '他'), 'た')
        self.assertEqual(self.reading('明日は雨だ。', '明日'), 'あした')
        self.assertIsNone(self.reading('明日の日本を担う', '明日'))
        self.assertIsNone(self.reading('料理が上手だ', '上手'))

    def test_heteronym_rules_post_war(self):
        known = {('表', 'おもて'), ('表', 'ひょう'), ('主', 'あるじ'), ('主', 'ぬし'), ('主', 'しゅ'), ('抱く', 'だく'),
                 ('抱く', 'いだく'), ('家', 'け'), ('家', 'いえ'), ('側', 'そば'), ('側', 'がわ'), ('傍', 'そば'),
                 ('傍', 'かたわら'), ('間', 'ま'), ('間', 'あいだ'), ('後', 'あと'), ('留まる', 'とどまる'), ('留まる', 'とまる')}
        cases = [('感情を表に出さない', '表', None, 'おもて'), ('コインの表が出た', '表', None, 'おもて'),
                 ('結果を表にまとめた', '表', None, None),
                 ('屋敷の主が客を迎えた', '主', None, 'あるじ'), ('我が主の命令', '主', None, 'あるじ'),
                 ('声の主は姉だった', '主', None, 'ぬし'), ('会議では主として予算を', '主', None, None), ('部屋の主', '主', None, None),
                 ('神剣の主として', '主', None, None),
                 ('赤ん坊を抱いている', '抱く', '抱い', 'だく'), ('少女に抱かれて眠った', '抱く', '抱か', None), ('また抱きたい', '抱く', '抱き', 'だく'),
                 ('不安を抱いている', '抱く', '抱い', None), ('疑問を抱かれる', '抱く', '抱か', None),
                 ('スミス家の人々', '家', None, 'け'), ('小さなボロ家', '家', None, None), ('友達の家に行く', '家', None, None),
                 ('彼の側にいる', '側', None, 'そば'), ('駅のすぐ側に', '側', None, 'そば'),
                 ('弱い者の側に立った', '側', None, None), ('彼の傍で眠る', '傍', None, 'そば'),
                 ('少し間を置いて', '間', None, 'ま'), ('返事をする間もなく', '間', None, 'ま'),
                 ('その間も雨は', '間', None, None), ('会話に間が空いた', '間', None, 'ま'),
                 ('この後、映画を', '後', None, 'あと'), ('その場に留まった', '留まる', '留まっ', 'とどまる'),
                 ('目に留まった', '留まる', '留まっ', None), ('鳥が木に留まる', '留まる', None, None)]
        for text, form, surface, reading in cases:
            begin = text.index(surface or form)
            self.assertEqual(context_reading(text, begin, surface or form, form, known), reading, text)

    def test_verb_and_adjective_rules(self):
        known = {(f, r) for f, rs in {'止める': 'とめる やめる', '抱く': 'だく いだく', '擦る': 'する こする さする', '弾く': 'ひく はじく',
                                      '解く': 'とく ほどく', '堪える': 'こらえる たえる', '被る': 'かぶる こうむる', '吐く': 'はく つく', '来る': 'くる きたる',
                                      '辛い': 'つらい からい', '開く': 'ひらく あく', '空く': 'あく すく', '描く': 'えがく かく'}.items() for r in rs.split()}
        cases = [('動きを止めた', '止める', '止め', 'とめる'), ('時間を止める', '止める', None, 'とめる'),
                 ('自分を抱いて', '抱く', '抱い', 'だく'), ('猫を抱いて寝た', '抱く', '抱い', 'だく'), ('野望を抱いて', '抱く', '抱い', None),
                 ('眠い目を擦りながら', '擦る', '擦り', 'こする'), ('ごしごしと擦った', '擦る', '擦っ', 'こする'),
                 ('頬を擦りつけた', '擦る', '擦り', 'こする'), ('マッチを擦った', '擦る', '擦っ', None), ('背中を擦った', '擦る', '擦っ', None),
                 ('ピアノを弾いた', '弾く', '弾い', 'ひく'), ('攻撃を弾いた', '弾く', '弾い', 'はじく'), ('指で弾いた', '弾く', '弾い', 'はじく'),
                 ('弾かれたように顔を上げた', '弾く', '弾か', 'はじく'), ('何を弾くか', '弾く', None, None), ('何のために弾くんだ', '弾く', None, None), ('ギターの弦を弾く', '弾く', None, None),
                 ('紐を解いた', '解く', '解い', 'ほどく'), ('謎を解いた', '解く', '解い', None),
                 ('涙を堪えた', '堪える', '堪え', 'こらえる'), ('堪えきれずに', '堪える', '堪え', 'こらえる'), ('痛みに堪える', '堪える', None, None),
                 ('被害を被った', '被る', '被っ', 'こうむる'), ('帽子を被った', '被る', '被っ', None),
                 ('ため息を吐いた', '吐く', '吐い', 'つく'), ('血を吐いた', '吐く', '吐い', None),
                 ('来るべきではなかった', '来る', None, 'くる'), ('来るべき日', '来る', None, None),
                 ('辛そうに笑った', '辛い', '辛', 'つらい'), ('辛くなる', '辛い', '辛く', 'つらい'), ('辛いカレー', '辛い', None, 'からい'),
                 ('辛くも逃げた', '辛い', '辛く', None), ('見辛い', '辛い', None, None), ('辛すぎる', '辛い', '辛', None),
                 ('絵を描いた', '描く', '描い', 'かく'), ('漫画に描かれた', '描く', '描か', 'かく'), ('油絵を描く', '描く', None, None),
                 ('弧を描いた', '描く', '描い', None), ('壁に穴が開いた', '開く', '開い', 'あく'), ('落とし穴が開いた', '開く', '開い', None), ('穴の空いた靴', '空く', '空い', 'あく'),
                 ('鼻を右手で擦って', '擦る', '擦っ', 'こする'), ('お腹を擦った', '擦る', '擦っ', 'さする'), ('止めに入った', '止める', '止め', 'とめる'),
                 ('船に空いた四角い穴', '空く', '空い', 'あく'), ('兄が描いたあの絵', '描く', '描い', None), ('兄が描いた絵', '描く', '描い', 'かく'),
                 ('描いた絵画', '描く', '描い', None), ('汚名を被った', '被る', '被っ', None)]
        for text, form, surface, reading in cases:
            begin = text.index(surface or form)
            self.assertEqual(context_reading(text, begin, surface or form, form, known), reading, text)

    def test_kata_and_nochi_rules(self):
        known = {('方', 'かた'), ('方', 'ほう'), ('後', 'あと'), ('後', 'のち'), ('後', 'ご')}
        cases = [('あのお方は', '方', 'かた'), ('お三方が来た', '方', 'かた'), ('紛う方なき本物', '方', 'かた'),
                 ('この方は私の恩人です', '方', 'かた'), ('その方は', '方', None), ('この方がいい', '方', 'ほう'),
                 ('この方に向かって', '方', None), ('教えてくださった方がいた', '方', 'かた'),
                 ('先に帰られた方がいい', '方', 'ほう'), ('助手の方に聞いた', '方', None), ('助手の方は親切だ', '方', 'かた'),
                 ('彼は、後に有名な作家となった', '後', 'のち'), ('後に分かったことだが', '後', 'のち'),
                 ('しかる後に', '後', 'のち'), ('それから後、二人は', '後', 'のち'), ('後の世に伝える', '後', 'のち'),
                 ('食事の後に散歩した', '後', None), ('、後に続く', '後', None), ('、後にいる者', '後', None),
                 ('後の世話を頼む', '後', None)]
        for text, form, reading in cases:
            self.assertEqual(context_reading(text, text.index(form), form, form, known), reading, text)

    def test_nani_before_ka_suru_and_verbs_nan_before_counters(self):
        for text in ('何か食べたい。', '何してるの？', '何？', '何食べる？'):
            self.assertEqual(self.reading(text, '何'), 'なに', text)
        for text in ('何ですか。', '何の話だ。', '何だって？'):  # なん by cue, shown (T490)
            self.assertEqual(self.reading(text, '何'), 'なん', text)
        for text in ('何年も待った。', '何冊ある？', '何百人も来た。', '何曜日ですか。'):
            self.assertIsNone(self.reading(text, '何'), text)  # Sudachi's なん stays

    def test_juu_after_a_stretch_of_time_or_a_place(self):
        for text in ('一日中寝ていた。', '一晩中起きていた。', '今日中に出す。', '世界中に広まった。', '家中を探した。', '体中が痛い。'):
            self.assertEqual(self.reading(text, '中'), 'じゅう', text)
        for text in ('授業中に寝た。', '今週中に出す。', '数日中に届く。', '一両日中に決まる。', '箱の中に入れた。'):
            self.assertIsNone(self.reading(text, '中'), text)  # Sudachi's ちゅう/なか stays

    def test_common_homographs(self):
        cases = [('この種の本', '種', 'しゅ'), ('数種の気体', '種', 'しゅ'), ('種をまく', '種', None),
                 ('他の追随を許さない', '他', 'た'), ('他言語から', '他', 'た'), ('他の人', '他', None),
                 ('木の下で休む', '下', 'した'), ('先生の指導の下で学ぶ', '下', 'もと'), ('机の下に', '下', None),
                 ('琴の音が聞こえる', '音', 'ね'), ('ぐうの音も出ない', '音', 'ね'), ('雨の音', '音', None),
                 ('こんな風に書く', '風', 'ふう'), ('知らない風を装う', '風', 'ふう'), ('花びらが風に舞う', '風', 'かぜ'),
                 ('風が吹く', '風', 'かぜ'), ('西洋風の家', '風', None)]
        for text, form, reading in cases:
            self.assertEqual(self.reading(text, form), reading, text)

    def test_kata_hou_ma_aida_ato(self):
        cases = [('あの方をご存知ですか', '方', 'かた'), ('あの方がいい', '方', 'ほう'), ('とても素敵な方です', '方', 'かた'),
                 ('どんな方なの', '方', 'かた'), ('担当の方はどなたですか', '方', 'かた'), ('ドイツの方ですか', '方', 'かた'),
                 ('女性の方が多い', '方', None), ('ホテルの方へ歩く', '方', 'ほう'), ('高血圧の方はいらっしゃいますか', '方', 'かた'),
                 ('一緒にやる方がいいよ', '方', 'ほう'), ('北の方へ行く', '方', None), ('得意な方だ', '方', None),
                 ('いつの間にか寝ていた', '間', 'ま'), ('一瞬の間があった', '間', 'ま'), ('またたく間に', '間', 'ま'),
                 ('この間、駅で会った', '間', 'あいだ'), ('その間に', '間', None), ('長い間待った', '間', None),
                 ('後五分で着く', '後', 'あと'), ('後数秒で', '後', 'あと'), ('その後二人は', '後', None),
                 ('五年後三月に', '後', None), ('購入後２日', '後', None), ('後で電話する', '後', None)]
        for text, form, reading in cases:
            self.assertEqual(self.reading(text, form), reading, text)

    def test_cue_rules_round_5e(self):
        cases = [('何やってるの？', '何', 'なに'), ('何に使うの？', '何', 'なに'), ('何ごっこ？', '何', 'なに'),
                 ('何にしても', '何', None), ('何になる', '何', None),
                 ('彼女は今医者だ', '今', 'いま'), ('今学期は', '今', None),
                 ('外の乗客と', '外', 'ほか'), ('待つ外はない', '外', 'ほか'), ('より外に道はない', '外', 'ほか'),
                 ('外の方が気持ちいい', '外', None), ('家の外に出る', '外', None),
                 ('床に就く', '床', 'とこ'), ('床から起きる', '床', 'とこ'), ('床に座る', '床', None),
                 ('尼君が来た', '君', 'ぎみ'), ('山田君が来た', '君', None), ('尼になる', '尼', 'あま'),
                 ('金は銀より重い', '金', 'きん'), ('雄弁は銀、沈黙は金', '金', 'きん'), ('金のくさり', '金', 'きん'),
                 ('金を貸す', '金', 'かね'), ('金は少しある', '金', None)]  # no cue: the かね default (DEFAULT_READINGS)
        for text, form, reading in cases:
            self.assertEqual(self.reading(text, form), reading, text)
        known = {('入る', 'いる'), ('入る', 'はいる')}
        for text, reading in (('月をながめ入っていた', 'いる'), ('郷に入っては', 'いる'), ('お金が少し入っている', None)):
            begin = text.index('入')
            self.assertEqual(context_reading(text, begin, text[begin:begin + 2], '入る', known), reading, text)

    def test_hitoke_needs_a_cue(self):
        for text in ('人気のない路地', '人気も無い', '人気が少ない', '人気が絶えた', '周囲に人気がない', '人気がない場所に',
                     '廊下は人気がなく静か', '夜の公園は人気がまったくなかった', '辺りに人気はなかった', '駐車場は人気がない', '事務所に人気がない'):
            self.assertEqual(self.reading(text, '人気'), 'ひとけ', text)
        self.assertEqual(self.reading('人気のない奴だ', '人気'), 'にんき')  # before the のない rule
        for text in ('この店は人気がない', '茨城県は人気がない', '海外では人気がない', '国内では人気がない', '人気がない',
                     'この作家はまだ人気がない', '作家は人気がない', '市場では人気がない', 'パン屋は人気がない',
                     '驚くほど人気がない', 'この店は全く人気がない', '北海道では人気がない', '長所は人気がないことだ'):
            self.assertIsNone(self.reading(text, '人気'), text)  # no cue: Sudachi's にんき

    def test_iru_after_ki_ni_and_jin_after_places(self):
        known = {('入る', 'いる'), ('入る', 'はいる'), ('人', 'じん'), ('人', 'ひと'), ('人', 'にん')}
        for text, reading in (('服が気に入っている', 'いる'), ('家族水入らずで', 'いる'), ('部屋に入った', None),
                              ('水が入らない', None)):
            begin = text.index('入')
            self.assertEqual(context_reading(text, begin, text[begin:begin + 2], '入る', known), reading, text)
        self.assertEqual(self.reading('カナダ人です', '人', known=known), 'じん')
        place = ('名詞', '固有名詞', '地名', '一般', '*', '*')
        self.assertEqual(context_reading('東京人は', 2, '人', '人', known, place), 'じん')
        self.assertIsNone(context_reading('東京人は', 2, '人', '人', known))
        self.assertIsNone(context_reading('東京人は', 2, '人', '人', known, ('名詞', '普通名詞', '一般', '*', '*', '*')))

    def test_only_the_line_and_listed_readings(self):
        self.assertIsNone(self.reading('舞台の\n上手から', '上手'))
        self.assertIsNone(self.reading('人気\nのない', '人気'))
        self.assertIsNone(self.reading('人気のない', '人気', known={('人気', 'にんき')}))
        self.assertIsNone(self.reading('人気のない', '人気', known=()))  # no frequency list: no rules


class DefaultReadingsTest(unittest.TestCase):
    def test_table_and_hand_picked(self):
        self.assertEqual(DEFAULT_READINGS['身体', 'しんたい'], 'からだ')  # default-readings.tsv
        self.assertEqual(DEFAULT_READINGS['私', 'わたくし'], 'わたし')
        self.assertTrue(all(reading != sudachi for (_, sudachi), reading in DEFAULT_READINGS.items()))

    def test_split_suffix(self):
        from yurigana.readings import split_suffix
        sfx, noun, pron, part = ('接尾辞', '名詞的', '一般'), ('名詞', '普通名詞', '一般'), ('代名詞', '*', '*'), ('助詞', '格助詞', '*')
        self.assertEqual(split_suffix('いつ家に', 2, '家', 'や', sfx, pron), 'いえ')
        self.assertEqual(split_suffix('一日中雨が', 3, '雨', 'う', sfx, noun), 'あめ')  # 一|日中: a time span
        self.assertIsNone(split_suffix('豪雨が', 1, '雨', 'う', sfx, noun))
        self.assertIsNone(split_suffix('いつ家に', 2, '家', 'や', noun, pron))  # not Sudachi's suffix
        self.assertEqual(split_suffix('矢は的に', 2, '的', 'てき', sfx, part), 'まと')
        self.assertIsNone(split_suffix('アタシ的に', 3, '的', 'てき', sfx, pron))
        self.assertIsNone(split_suffix('私は的な', 2, '的', 'てき', sfx, part))
        self.assertIsNone(split_suffix('Ａ君が', 1, '君', 'くん', sfx, ('補助記号', '一般', '*')))
        self.assertEqual(split_suffix('「君が', 1, '君', 'くん', sfx, None), 'きみ')

    def test_glued(self):
        self.assertTrue(glued('郵便局側の', 3, 4))
        self.assertTrue(glued('今学期', 0, 1))
        self.assertTrue(glued('第3位', 2, 3))
        self.assertTrue(glued('ダウンロード時に', 6, 7))
        self.assertFalse(glued('川の側に', 2, 3))
        self.assertFalse(glued('身体中', 0, 2))  # only one-character words


if __name__ == '__main__':
    unittest.main()
