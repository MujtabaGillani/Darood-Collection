import React, { useState } from 'react';
import { View, Text } from 'react-native';
import Svg, { Circle, G, Line, Path, Rect, Text as SvgText } from 'react-native-svg';

import { useTheme } from '../context/ThemeContext';
import { chartPalette } from '../theme/colors';
import { fmt } from './UI';

const HEIGHT = 200;
const PAD = { top: 16, right: 12, bottom: 26, left: 40 };

/**
 * Multi-series trend chart. Draws grouped bars when there is a single bucket
 * (e.g. "Today") and lines otherwise — matching the web behaviour.
 *
 * props: labels: string[], datasets: [{ label, data: number[] }]
 */
export default function TrendChart({ labels = [], datasets = [] }) {
  const { colors } = useTheme();
  const [width, setWidth] = useState(0);

  const series = datasets.filter((d) => Array.isArray(d.data));
  const allValues = series.flatMap((d) => d.data);
  const max = Math.max(1, ...allValues);
  const single = labels.length <= 1;

  const chartW = Math.max(0, width - PAD.left - PAD.right);
  const chartH = HEIGHT - PAD.top - PAD.bottom;

  const x = (i) => {
    if (labels.length <= 1) return PAD.left + chartW / 2;
    return PAD.left + (chartW * i) / (labels.length - 1);
  };
  const y = (v) => PAD.top + chartH - (chartH * v) / max;

  // y grid lines at 0, 50%, 100%
  const gridVals = [0, max / 2, max];

  return (
    <View>
      <View onLayout={(e) => setWidth(e.nativeEvent.layout.width)}>
        {width > 0 && (
          <Svg width={width} height={HEIGHT}>
            {/* grid + y labels */}
            {gridVals.map((gv, idx) => (
              <G key={idx}>
                <Line
                  x1={PAD.left}
                  x2={width - PAD.right}
                  y1={y(gv)}
                  y2={y(gv)}
                  stroke={colors.border}
                  strokeWidth={1}
                />
                <SvgText x={PAD.left - 6} y={y(gv) + 3} fontSize="9" fill={colors.muted} textAnchor="end">
                  {fmt(Math.round(gv))}
                </SvgText>
              </G>
            ))}

            {/* data */}
            {single
              ? series.map((d, si) => {
                  const color = chartPalette[si % chartPalette.length];
                  const barW = Math.min(48, chartW / (series.length + 1));
                  const groupW = barW * series.length;
                  const startX = PAD.left + chartW / 2 - groupW / 2;
                  const val = d.data[0] || 0;
                  const h = (chartH * val) / max;
                  return (
                    <Rect
                      key={si}
                      x={startX + si * barW}
                      y={PAD.top + chartH - h}
                      width={barW - 4}
                      height={h}
                      rx={4}
                      fill={color}
                    />
                  );
                })
              : series.map((d, si) => {
                  const color = chartPalette[si % chartPalette.length];
                  const path = d.data
                    .map((v, i) => `${i === 0 ? 'M' : 'L'} ${x(i)} ${y(v)}`)
                    .join(' ');
                  return (
                    <G key={si}>
                      <Path d={path} stroke={color} strokeWidth={2.5} fill="none" />
                      {d.data.map((v, i) => (
                        <Circle key={i} cx={x(i)} cy={y(v)} r={2.5} fill={color} />
                      ))}
                    </G>
                  );
                })}

            {/* x labels: first, middle, last */}
            {labels.map((lab, i) => {
              const show =
                labels.length <= 4 || i === 0 || i === labels.length - 1 || i === Math.floor(labels.length / 2);
              if (!show) return null;
              return (
                <SvgText
                  key={i}
                  x={x(i)}
                  y={HEIGHT - 8}
                  fontSize="9"
                  fill={colors.muted}
                  textAnchor={i === 0 ? 'start' : i === labels.length - 1 ? 'end' : 'middle'}
                >
                  {lab}
                </SvgText>
              );
            })}
          </Svg>
        )}
      </View>

      {/* legend with per-series totals */}
      <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: 12, justifyContent: 'center', marginTop: 6 }}>
        {series.map((d, si) => {
          const color = chartPalette[si % chartPalette.length];
          const total = d.data.reduce((a, b) => a + (b || 0), 0);
          return (
            <View key={si} style={{ flexDirection: 'row', alignItems: 'center', gap: 5 }}>
              <View style={{ width: 10, height: 10, borderRadius: 5, backgroundColor: color }} />
              <Text style={{ color: colors.text, fontSize: 12 }}>
                {d.label} · {fmt(total)}
              </Text>
            </View>
          );
        })}
      </View>
    </View>
  );
}
