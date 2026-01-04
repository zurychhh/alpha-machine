"""
Portfolio Allocation Service - 3 allocation strategies for capital distribution.

Strategies:
- CORE_FOCUS: 60% top signal, 30% next 3 (10% each), 10% cash
- BALANCED: 40% top signal, 50% next 4 (12.5% each), 10% cash
- DIVERSIFIED: 80% equally across top 5 (16% each), 20% cash
"""

from typing import List, Dict, Literal
import logging

logger = logging.getLogger(__name__)

# Type alias for allocation modes
AllocationMode = Literal["CORE_FOCUS", "BALANCED", "DIVERSIFIED"]


class PortfolioAllocator:
    """Allocates capital across signals based on selected strategy."""

    def allocate(
        self,
        ranked_signals: List[Dict],
        starting_capital: float,
        mode: AllocationMode,
    ) -> List[Dict]:
        """
        Allocate capital across ranked signals based on strategy.

        Args:
            ranked_signals: Output from SignalRanker.rank_signals()
            starting_capital: Total capital to invest (e.g., 50000)
            mode: Allocation strategy to use

        Returns:
            List of position allocations:
            [
                {
                    "signal": Signal object,
                    "allocation_pct": 0.60,
                    "allocation_dollars": 30000.00,
                    "shares": 34,
                    "position_type": "CORE" | "SATELLITE" | "EQUAL"
                },
                ...
            ]

        Raises:
            ValueError: If unknown allocation mode provided
        """
        if mode == "CORE_FOCUS":
            return self._allocate_core_focus(ranked_signals, starting_capital)
        elif mode == "BALANCED":
            return self._allocate_balanced(ranked_signals, starting_capital)
        elif mode == "DIVERSIFIED":
            return self._allocate_diversified(ranked_signals, starting_capital)
        else:
            raise ValueError(f"Unknown allocation mode: {mode}")

    def _allocate_core_focus(
        self, ranked_signals: List[Dict], capital: float
    ) -> List[Dict]:
        """
        CORE FOCUS allocation strategy.

        Distribution:
        - Top signal: 60% (CORE position)
        - Next 3 signals: 30% total (10% each, SATELLITE positions)
        - Cash reserve: 10%

        Best for: High conviction trading, fewer positions, concentrated bets.
        """
        positions = []

        if len(ranked_signals) == 0:
            logger.warning("No signals to allocate in CORE_FOCUS mode")
            return positions

        # Core position (60%)
        core_signal = ranked_signals[0]
        core_dollars = capital * 0.60
        entry_price = float(core_signal["signal"].entry_price or 100)
        core_shares = int(core_dollars / entry_price) if entry_price > 0 else 0

        positions.append(
            {
                "signal": core_signal["signal"],
                "allocation_pct": 0.60,
                "allocation_dollars": round(core_dollars, 2),
                "shares": core_shares,
                "position_type": "CORE",
                "rank": 1,
                "score": core_signal["score"],
            }
        )

        # Satellite positions (next 3, 10% each)
        satellite_capital_per = capital * 0.10
        for i in range(1, min(4, len(ranked_signals))):
            sat_signal = ranked_signals[i]
            entry_price = float(sat_signal["signal"].entry_price or 100)
            sat_shares = int(satellite_capital_per / entry_price) if entry_price > 0 else 0

            positions.append(
                {
                    "signal": sat_signal["signal"],
                    "allocation_pct": 0.10,
                    "allocation_dollars": round(satellite_capital_per, 2),
                    "shares": sat_shares,
                    "position_type": "SATELLITE",
                    "rank": i + 1,
                    "score": sat_signal["score"],
                }
            )

        logger.info(
            f"CORE_FOCUS: Allocated ${capital:.2f} across {len(positions)} positions"
        )
        return positions

    def _allocate_balanced(
        self, ranked_signals: List[Dict], capital: float
    ) -> List[Dict]:
        """
        BALANCED allocation strategy.

        Distribution:
        - Top signal: 40% (CORE position)
        - Next 4 signals: 50% total (12.5% each, SATELLITE positions)
        - Cash reserve: 10%

        Best for: Moderate diversification, still conviction-based.
        """
        positions = []

        if len(ranked_signals) == 0:
            logger.warning("No signals to allocate in BALANCED mode")
            return positions

        # Core position (40%)
        core_signal = ranked_signals[0]
        core_dollars = capital * 0.40
        entry_price = float(core_signal["signal"].entry_price or 100)
        core_shares = int(core_dollars / entry_price) if entry_price > 0 else 0

        positions.append(
            {
                "signal": core_signal["signal"],
                "allocation_pct": 0.40,
                "allocation_dollars": round(core_dollars, 2),
                "shares": core_shares,
                "position_type": "CORE",
                "rank": 1,
                "score": core_signal["score"],
            }
        )

        # Satellite positions (next 4, 12.5% each)
        satellite_capital_per = capital * 0.125
        for i in range(1, min(5, len(ranked_signals))):
            sat_signal = ranked_signals[i]
            entry_price = float(sat_signal["signal"].entry_price or 100)
            sat_shares = int(satellite_capital_per / entry_price) if entry_price > 0 else 0

            positions.append(
                {
                    "signal": sat_signal["signal"],
                    "allocation_pct": 0.125,
                    "allocation_dollars": round(satellite_capital_per, 2),
                    "shares": sat_shares,
                    "position_type": "SATELLITE",
                    "rank": i + 1,
                    "score": sat_signal["score"],
                }
            )

        logger.info(
            f"BALANCED: Allocated ${capital:.2f} across {len(positions)} positions"
        )
        return positions

    def _allocate_diversified(
        self, ranked_signals: List[Dict], capital: float
    ) -> List[Dict]:
        """
        DIVERSIFIED allocation strategy.

        Distribution:
        - Top 5 signals equally: 80% total (16% each, EQUAL positions)
        - Cash reserve: 20%

        Best for: Risk-averse trading, maximum diversification.
        """
        positions = []

        if len(ranked_signals) == 0:
            logger.warning("No signals to allocate in DIVERSIFIED mode")
            return positions

        # Equal weight across top 5 (or fewer if less available)
        num_positions = min(5, len(ranked_signals))
        allocation_per = 0.80 / num_positions
        capital_per = (capital * 0.80) / num_positions

        for i in range(num_positions):
            sig = ranked_signals[i]
            entry_price = float(sig["signal"].entry_price or 100)
            shares = int(capital_per / entry_price) if entry_price > 0 else 0

            positions.append(
                {
                    "signal": sig["signal"],
                    "allocation_pct": round(allocation_per, 4),
                    "allocation_dollars": round(capital_per, 2),
                    "shares": shares,
                    "position_type": "EQUAL",
                    "rank": i + 1,
                    "score": sig["score"],
                }
            )

        logger.info(
            f"DIVERSIFIED: Allocated ${capital:.2f} across {len(positions)} positions"
        )
        return positions

    def get_cash_reserve(self, mode: AllocationMode, capital: float) -> float:
        """
        Get cash reserve amount for given mode.

        Args:
            mode: Allocation strategy
            capital: Starting capital

        Returns:
            Cash reserve amount
        """
        reserves = {
            "CORE_FOCUS": 0.10,
            "BALANCED": 0.10,
            "DIVERSIFIED": 0.20,
        }
        return capital * reserves.get(mode, 0.10)

    def get_mode_description(self, mode: AllocationMode) -> Dict:
        """
        Get description of allocation mode.

        Args:
            mode: Allocation strategy

        Returns:
            Description dict with strategy details
        """
        descriptions = {
            "CORE_FOCUS": {
                "name": "Core Focus",
                "description": "Concentrated bets on highest conviction signals",
                "core_allocation": "60%",
                "satellite_count": 3,
                "satellite_allocation": "10% each",
                "cash_reserve": "10%",
                "risk_level": "High",
                "best_for": "High conviction, fewer positions",
            },
            "BALANCED": {
                "name": "Balanced",
                "description": "Moderate diversification with conviction core",
                "core_allocation": "40%",
                "satellite_count": 4,
                "satellite_allocation": "12.5% each",
                "cash_reserve": "10%",
                "risk_level": "Medium",
                "best_for": "Balance between conviction and diversification",
            },
            "DIVERSIFIED": {
                "name": "Diversified",
                "description": "Maximum diversification across top signals",
                "core_allocation": "N/A (equal weight)",
                "satellite_count": 5,
                "satellite_allocation": "16% each",
                "cash_reserve": "20%",
                "risk_level": "Low",
                "best_for": "Risk-averse, maximum diversification",
            },
        }
        return descriptions.get(mode, {})


# Singleton instance
portfolio_allocator = PortfolioAllocator()
