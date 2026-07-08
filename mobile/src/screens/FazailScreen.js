import React from 'react';
import { Text, View } from 'react-native';

import { Card, Screen } from '../components/UI';
import { useTheme } from '../context/ThemeContext';
import { dua, hadith, quran } from '../data/fazail';

function VerseCard({ index, text, refText }) {
  const { colors } = useTheme();
  return (
    <Card style={{ gap: 10, overflow: 'hidden' }}>
      {/* gold/teal accent bar, like the web card's ::before */}
      <View style={{ position: 'absolute', top: 0, left: 0, right: 0, height: 3, backgroundColor: colors.accent }} />
      <View
        style={{
          width: 34,
          height: 34,
          borderRadius: 17,
          backgroundColor: colors.primary,
          alignItems: 'center',
          justifyContent: 'center',
          alignSelf: 'flex-start',
        }}
      >
        <Text style={{ color: colors.accent, fontWeight: '700' }}>{index}</Text>
      </View>
      <Text
        style={{
          color: colors.text,
          fontSize: 19,
          lineHeight: 36,
          textAlign: 'right',
          writingDirection: 'rtl',
        }}
      >
        {text}
      </Text>
      <View
        style={{
          alignSelf: 'flex-start',
          backgroundColor: colors.primary,
          borderRadius: 999,
          paddingHorizontal: 14,
          paddingVertical: 5,
        }}
      >
        <Text style={{ color: '#fff', writingDirection: 'rtl' }}>{refText}</Text>
      </View>
    </Card>
  );
}

function SectionTitle({ children }) {
  const { colors } = useTheme();
  return (
    <Text
      style={{
        color: colors.primary,
        fontSize: 22,
        fontWeight: '800',
        textAlign: 'center',
        writingDirection: 'rtl',
        marginTop: 8,
      }}
    >
      {children}
    </Text>
  );
}

export default function FazailScreen() {
  const { colors } = useTheme();
  return (
    <Screen>
      <Text style={{ color: colors.primary, fontSize: 30, fontWeight: '800', textAlign: 'center', writingDirection: 'rtl' }}>
        درود شریف کے فضائل
      </Text>
      <Text style={{ color: colors.muted, textAlign: 'center', fontStyle: 'italic' }}>
        Verified verses & hadiths on the virtue of Darood
      </Text>

      <SectionTitle>قرآنِ کریم کی روشنی میں</SectionTitle>
      {quran.map((v, i) => (
        <VerseCard key={`q${i}`} index={i + 1} text={v.text} refText={v.ref} />
      ))}

      <SectionTitle>احادیثِ مبارکہ</SectionTitle>
      {hadith.map((h, i) => (
        <VerseCard key={`h${i}`} index={i + 1} text={h.text} refText={h.ref} />
      ))}

      <Text
        style={{
          color: colors.primary,
          fontSize: 22,
          textAlign: 'center',
          writingDirection: 'rtl',
          marginVertical: 16,
          lineHeight: 40,
        }}
      >
        {dua}
      </Text>
    </Screen>
  );
}
