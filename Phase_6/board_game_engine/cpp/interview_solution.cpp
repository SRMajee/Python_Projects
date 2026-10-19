/*
 * Board Game Engine - Interview Solution (C++)
 *
 * 1. Primary Capabilities:
 *   - Command pattern: MoveCommand with execute/undo
 *   - Snake & Ladder board with configurable map
 *   - Turn-based engine, dice, win detection
 *   - Concurrency Extension: mutex on game state
 *
 * 2. Error Handling:
 *   - runtime_error on game-over play, returns false on invalid move
 *
 * 3. Out Of Scope:
 *   - Chess validation, AI, network play, persistence, replays
 */
#include<bits/stdc++.h>
using namespace std;

struct Player { string name; int pos = 0; };

class Board {
    int sz; unordered_map<int,int> snakes, ladders;
public:
    Board(int s, unordered_map<int,int> sn={}, unordered_map<int,int> ld={}) : sz(s), snakes(sn), ladders(ld) {}
    int size() const { return sz; }
    int process(int p) const { auto it=snakes.find(p); if(it!=snakes.end()) return it->second;
        it=ladders.find(p); return it!=ladders.end() ? it->second : p; }
};

struct Move { Player* p; int old_pos, dice;
    bool exec(const Board& b) { int np = p->pos + dice; if(np>b.size()) return false; p->pos=b.process(np); return true; }
    void undo() { p->pos = old_pos; }
};

class Engine {
    Board board; vector<Player> ps; int turn=0;
    vector<Move> hist; Player* winner=nullptr; mutex mtx;
public:
    Engine(Board b) : board(move(b)) {}
    void add(const string& n) { lock_guard<mutex> lk(mtx); ps.push_back({n}); }
    pair<int,bool> play(int d) { lock_guard<mutex> lk(mtx);
        if(winner) throw runtime_error("over");
        auto& p = ps[turn%ps.size()]; Move m{&p, p.pos, d};
        bool ok = m.exec(board); if(ok) { hist.push_back(m); if(p.pos==board.size()) winner=&p; }
        turn++; return {p.pos, p.pos==board.size()}; }
    bool undo() { lock_guard<mutex> lk(mtx); if(hist.empty()) return false;
        hist.back().undo(); hist.pop_back(); turn--; winner=nullptr; return true; }
};

int main() {
    Board b(20, {{15,5}}, {{3,12}});
    Engine e(b); e.add("A"); e.add("B");
    auto [pos, won] = e.play(3); assert(pos == 12); // ladder
    e.undo();
    e.play(4); e.play(1); // A->4, B->1
    auto [pos2, _] = e.play(11); assert(pos2 == 5); // 4+11=15 -> snake -> 5
    cout << "Interview C++ Board Game passed!" << endl;
}
