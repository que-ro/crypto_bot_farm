from scripts.interfaces import StrategyResultLabellerInterface
import numpy as np

class CustomLabeller1(StrategyResultLabellerInterface):

    def __init__(self, df_products):

        self.name = 'CustomLabeller1'

        #Check parameters
        assert 'gain_loss_percentage' in df_products, 'The dataframe should contain a "gain_loss_percentage" column'
        assert 'nb_sold_order' in df_products, 'The dataframe should contain a "nb_sold_order" column'

        #Set variable
        self.df_products = df_products

    # region Interfaces method

    @staticmethod
    def get_name() -> str:
        return 'CustomLabeller1'

    def get_df_product_with_strat_result_label(self) -> object:
        # Init result_label column
        self.df_products['result_label'] = 0

        # Init condition determining a success of a strategy
        is_gain_loss_perc_sup = self.df_products['gain_loss_percentage'] >= 0.2
        is_nb_sold_sup_2 = self.df_products['nb_sold_order'] > 0

        # Set success
        self.df_products['result_label'] = np.where(is_gain_loss_perc_sup & is_nb_sold_sup_2, 1, 0)

        return self.df_products

    # endregion