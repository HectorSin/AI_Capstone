import { memo } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';

type NavigationHeaderProps = {
  title?: string;
  onBack: () => void;
  rightButton?: {
    text: string;
    onPress: () => void;
    disabled?: boolean;
    loading?: boolean;
    variant?: 'primary' | 'secondary';
  };
};

function NavigationHeaderComponent({ title, onBack, rightButton }: NavigationHeaderProps) {
  const getRightButtonTextStyle = () => {
    if (rightButton?.disabled) {
      return styles.saveTextDisabled;
    }
    return rightButton?.variant === 'secondary' ? styles.shareText : styles.saveText;
  };

  return (
    <View style={styles.headerBar}>
      <Pressable
        onPress={onBack}
        hitSlop={8}
        style={({ pressed }) => [styles.headerButton, pressed && styles.buttonPressed]}
      >
        <Text style={styles.backText}>뒤로</Text>
      </Pressable>
      {title ? <Text style={styles.headerTitle}>{title}</Text> : <View style={styles.spacer} />}
      {rightButton ? (
        <Pressable
          disabled={rightButton.disabled}
          onPress={rightButton.onPress}
          hitSlop={8}
          style={({ pressed }) => [
            styles.headerButton,
            rightButton.disabled && styles.headerButtonDisabled,
            pressed && !rightButton.disabled && styles.buttonPressed,
          ]}
        >
          <Text style={getRightButtonTextStyle()}>{rightButton.text}</Text>
        </Pressable>
      ) : (
        <View style={styles.headerButton} />
      )}
    </View>
  );
}

export const NavigationHeader = memo(NavigationHeaderComponent);

const styles = StyleSheet.create({
  headerBar: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 14,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: '#e5e7eb',
    backgroundColor: '#ffffff',
  },
  headerButton: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    minWidth: 50,
  },
  headerButtonDisabled: {
    opacity: 0.4,
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#111827',
  },
  backText: {
    fontSize: 14,
    color: '#2563eb',
  },
  saveText: {
    fontSize: 14,
    color: '#2563eb',
    fontWeight: '600',
  },
  shareText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#2563eb',
  },
  saveTextDisabled: {
    fontSize: 14,
    color: '#9ca3af',
    fontWeight: '600',
  },
  buttonPressed: {
    opacity: 0.5,
  },
  spacer: {
    flex: 1,
  },
});
