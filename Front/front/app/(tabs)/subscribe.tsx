import { StyleSheet, Text, View } from 'react-native';

export default function SubscribeScreen() {
  return (
    <View style={styles.container}>
      <Text style={styles.title}>Subscribe</Text>
      <Text style={styles.subtitle}>Connect subscription plans or premium content access in this tab.</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 24,
  },
  title: {
    fontSize: 24,
    fontWeight: '600',
    marginBottom: 12,
  },
  subtitle: {
    fontSize: 16,
    color: '#4b5563',
    textAlign: 'center',
  },
});
