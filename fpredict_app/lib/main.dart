import 'package:flutter/material.dart';
import 'package:supabase_flutter/supabase_flutter.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  
  await Supabase.initialize(
    url: 'https://agojvvfjajkkpqohehcm.supabase.co',
    anonKey: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFnb2p2dmZqYWpra3Bxb2hlaGNtIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODEzNDkyMzEsImV4cCI6MjA5NjkyNTIzMX0.VVKkTvlGRvQWKhOo_GzReyN9zUaw0J6CKm3voY-V6vU',
  );

  runApp(const FPredictApp());
}

class FPredictApp extends StatelessWidget {
  const FPredictApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'FPredict Cockpit',
      theme: ThemeData(
        useMaterial3: true,
        colorScheme: ColorScheme.fromSeed(
          seedColor: const Color(0xFF673AB7),
          brightness: Brightness.dark,
          surface: const Color(0xFF121212),
        ),
        textTheme: GoogleFonts.barlowTextTheme(ThemeData.dark().textTheme),
      ),
      home: const MainNavigationScreen(),
    );
  }
}

class MainNavigationScreen extends StatefulWidget {
  const MainNavigationScreen({super.key});

  @override
  State<MainNavigationScreen> createState() => _MainNavigationScreenState();
}

class _MainNavigationScreenState extends State<MainNavigationScreen> {
  int _currentIndex = 0;

  final List<Widget> _tabs = [
    const DashboardTab(),
    const QuantumLabTab(), // The new Interactive Lab
    const HealthTab(),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('FPREDICT', 
          style: GoogleFonts.orbitron(fontWeight: FontWeight.bold, letterSpacing: 2)
        ),
        actions: [
          IconButton(icon: const Icon(Icons.notifications_none), onPressed: () {}),
          const CircleAvatar(radius: 16, backgroundColor: Colors.deepPurple, child: Icon(Icons.person, size: 18)),
          const SizedBox(width: 16),
        ],
      ),
      body: _tabs[_currentIndex],
      bottomNavigationBar: NavigationBar(
        selectedIndex: _currentIndex,
        onDestinationSelected: (index) => setState(() => _currentIndex = index),
        destinations: const [
          NavigationDestination(icon: Icon(Icons.dashboard_outlined), selectedIcon: Icon(Icons.dashboard), label: 'Stats'),
          NavigationDestination(icon: Icon(Icons.science_outlined), selectedIcon: Icon(Icons.science), label: 'Lab'),
          NavigationDestination(icon: Icon(Icons.sensors_outlined), selectedIcon: Icon(Icons.sensors), label: 'Health'),
        ],
      ),
    );
  }
}

class DashboardTab extends StatelessWidget {
  const DashboardTab({super.key});

  @override
  Widget build(BuildContext context) {
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        _buildBankrollCard(),
        const SizedBox(height: 24),
        const Text('System Summary', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
        const SizedBox(height: 12),
        Row(
          children: [
            Expanded(child: _buildSmallStat('Win Rate', '67.6%', Colors.blue)),
            const SizedBox(width: 16),
            Expanded(child: _buildSmallStat('Accuracy', '52.3%', Colors.green)),
          ],
        ),
      ],
    );
  }

  Widget _buildBankrollCard() {
    return Container(
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        gradient: LinearGradient(colors: [Colors.deepPurple.shade700, Colors.deepPurple.shade400]),
        borderRadius: BorderRadius.circular(24),
      ),
      child: const Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text('Total Bankroll', style: TextStyle(color: Colors.white70)),
          Text('\$1,542.44', style: TextStyle(fontSize: 32, fontWeight: FontWeight.bold, color: Colors.white)),
          SizedBox(height: 8),
          Text('+\$542.44 today', style: TextStyle(color: Colors.greenAccent, fontWeight: FontWeight.bold)),
        ],
      ),
    );
  }

  Widget _buildSmallStat(String label, String value, Color color) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(color: Colors.white.withValues(alpha: 0.05), borderRadius: BorderRadius.circular(16)),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(label, style: const TextStyle(color: Colors.white54, fontSize: 12)),
          Text(value, style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold, color: color)),
        ],
      ),
    );
  }
}

class QuantumLabTab extends StatefulWidget {
  const QuantumLabTab({super.key});
  @override
  State<QuantumLabTab> createState() => _QuantumLabTabState();
}

class _QuantumLabTabState extends State<QuantumLabTab> {
  String? _homeTeamId;
  String? _awayTeamId;
  bool _isProcessing = false;
  Map<String, dynamic>? _prediction;

  final client = Supabase.instance.client;

  Future<void> _requestPrediction() async {
    if (_homeTeamId == null || _awayTeamId == null) return;
    
    setState(() {
      _isProcessing = true;
      _prediction = null; // Clear previous result
    });
    
    // 1. Submit Request
    final insertResponse = await client.from('prediction_requests').insert({
      'home_team_id': _homeTeamId,
      'away_team_id': _awayTeamId,
      'status': 'PENDING'
    }).select().single();

    final requestId = insertResponse['id'];

    // 2. Poll for Completion (Wait for AI Brain)
    bool isDone = false;
    int attempts = 0;
    while (!isDone && attempts < 30) { // Increased to 30 attempts (60 seconds)
      await Future.delayed(const Duration(seconds: 2));
      final statusRes = await client
          .from('prediction_requests')
          .select('status')
          .eq('id', requestId)
          .single();
      
      if (statusRes['status'] == 'COMPLETED') {
        isDone = true;
      }
      attempts++;
    }

    // 3. Fetch the EXACT prediction linked to this specific request
    final response = await client
        .from('predictions')
        .select()
        .eq('version_id', 'live-$requestId')
        .limit(1);
    
    if (response.isNotEmpty) {
      setState(() {
        _prediction = response.first;
        _isProcessing = false;
      });
    } else {
      print('Warning: Prediction not found for requestId: $requestId');
      setState(() => _isProcessing = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return RefreshIndicator(
      onRefresh: () async {
        // Force re-fetch of data
        setState(() {});
      },
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          const Text('Interactive Match Simulation', style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold)),
          const Text('Select two teams to generate quantum insights.', style: TextStyle(color: Colors.grey)),
          const SizedBox(height: 24),
          _buildTeamSelectors(),
          const SizedBox(height: 24),
          _buildActionButton(),
          const SizedBox(height: 32),
          if (_prediction != null) _buildResultView(),
        ],
      ),
    );
  }

  Widget _buildTeamSelectors() {
    return FutureBuilder<List<Map<String, dynamic>>>(
      future: client.from('teams').select('id, team_name').order('team_name'),
      builder: (context, snapshot) {
        if (!snapshot.hasData) return const LinearProgressIndicator();
        final teams = snapshot.data!;
        
        return Column(
          children: [
            _buildDropdown('Home Team', _homeTeamId, teams, (val) => setState(() => _homeTeamId = val)),
            const SizedBox(height: 16),
            _buildDropdown('Away Team', _awayTeamId, teams, (val) => setState(() => _awayTeamId = val)),
          ],
        );
      },
    );
  }

  Widget _buildDropdown(String label, String? value, List<Map<String, dynamic>> teams, Function(String?) onChanged) {
    return DropdownButtonFormField<String>(
      decoration: InputDecoration(
        labelText: label,
        border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
        filled: true,
        fillColor: Colors.white.withValues(alpha: 0.03),
      ),
      value: value,
      items: teams.map((t) => DropdownMenuItem(value: t['id'].toString(), child: Text(t['team_name']))).toList(),
      onChanged: onChanged,
    );
  }

  Widget _buildActionButton() {
    return SizedBox(
      width: double.infinity,
      height: 56,
      child: ElevatedButton.icon(
        icon: _isProcessing ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2)) : const Icon(Icons.bolt),
        label: Text(_isProcessing ? 'PROCESSING ENGINE...' : 'GENERATE QUANTUM INSIGHT'),
        style: ElevatedButton.styleFrom(
          backgroundColor: Colors.deepPurple,
          foregroundColor: Colors.white,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
        ),
        onPressed: _isProcessing ? null : _requestPrediction,
      ),
    );
  }

  Widget _buildResultView() {
    final probs = _prediction!['win_probability'] as Map<String, dynamic>;
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: Colors.white.withValues(alpha: 0.05),
        borderRadius: BorderRadius.circular(24),
        border: Border.all(color: Colors.white10),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Row(
            children: [
              Icon(Icons.auto_awesome, color: Colors.amber, size: 18),
              SizedBox(width: 8),
              Text('QUANTUM RESULT', style: TextStyle(fontWeight: FontWeight.bold, color: Colors.amber)),
            ],
          ),
          const SizedBox(height: 16),
          Text(_prediction!['tactical_narrative'] ?? 'Analysis complete.', style: const TextStyle(fontSize: 16, height: 1.4)),
          const SizedBox(height: 24),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              _buildMetric('Home Win', '${((probs['home'] ?? 0) * 100).toInt()}%'),
              _buildMetric('Draw', '${((probs['draw'] ?? 0) * 100).toInt()}%'),
              _buildMetric('Away Win', '${((probs['away'] ?? 0) * 100).toInt()}%'),
            ],
          ),
          const SizedBox(height: 20),
          Row(
            children: [
              _buildMetric('Kelly Stake', '${((_prediction!['kelly_stake'] ?? 0) * 100).toStringAsFixed(1)}%'),
              const Spacer(),
              _buildMetric('Advantage', '+${((_prediction!['edge_value'] ?? 0) * 100).toStringAsFixed(1)}%'),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildMetric(String label, String value) {
    return Column(
      children: [
        Text(label, style: const TextStyle(fontSize: 10, color: Colors.white54)),
        Text(value, style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
      ],
    );
  }
}

class HealthTab extends StatelessWidget {
  const HealthTab({super.key});

  @override
  Widget build(BuildContext context) {
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        const Text('Engine Status', style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold)),
        const SizedBox(height: 24),
        _buildHealthItem('Knowledge Layer', 'ACTIVE', Icons.psychology, Colors.amber),
        _buildHealthItem('Supabase Remote', 'CONNECTED', Icons.cloud_done, Colors.green),
        _buildHealthItem('Postgres Local', 'CONNECTED', Icons.storage, Colors.green),
        _buildHealthItem('NLP Pipeline', 'HEALTHY', Icons.psychology, Colors.blue),
      ],
    );
  }

  Widget _buildHealthItem(String service, String status, IconData icon, Color color) {
    return ListTile(
      leading: Icon(icon, color: color),
      title: Text(service),
      subtitle: Text(status, style: TextStyle(color: color, fontWeight: FontWeight.bold, fontSize: 12)),
    );
  }
}
